#!/bin/sh
# Run in the arm64 Debian trixie VM: lays MediaTagger out on a drive — app, third-party packages for the Pi's Python 3.13
# and the libmpv2 .debs the Pi lacks (from APTPI, default ~/aptpi, a Pi-like apt root). Never touches <drive>/.mediatagger/.
# Usage: sh drive/build-drive.sh <drive mount point>
[ -n "$1" ] || { echo "usage: sh drive/build-drive.sh <drive>" >&2; exit 2; }
lib="$1/mediatagger/lib-linux-aarch64-cp313"
rm -rf "$lib"
requirements=$(mktemp)
(cd "$(dirname "$0")/.." && uv export --frozen --no-dev --no-hashes --no-emit-project) > "$requirements"
uv pip install -q --python /usr/bin/python3.13 --target "$lib" -r "$requirements" || exit 1
rm -f "$requirements"
python3.13 -m compileall -q --invalidation-mode unchecked-hash -x /deploy_lib/ "$lib"
debs="$1/mediatagger/debs"
rm -rf "$debs"
archives="${APTPI:-$HOME/aptpi}/var/cache/apt/archives"
if ! ls "$archives"/*.deb > /dev/null 2>&1; then
  echo "no .deb in $archives" >&2
  exit 1
fi
mkdir -p "$debs"
cp "$archives"/*.deb "$debs"
(cd "$debs" && apt-ftparchive packages . > Packages)
sh "$(dirname "$0")"/update-drive.sh "$1" || exit 1
: > "$1/.metadata_never_index"
sync
echo "Drive ready: $1/mediatagger"
