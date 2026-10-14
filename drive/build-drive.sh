#!/bin/sh
lib="$1/mediatagger/lib-linux-aarch64-cp313"
rm -rf "$lib"
requirements=$(mktemp)
uv export --frozen --no-dev --no-hashes --no-emit-project > "$requirements"
uv pip install -q --python /usr/bin/python3.13 --target "$lib" -r "$requirements"
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
sh "$(dirname "$0")"/update-drive.sh "$1"
