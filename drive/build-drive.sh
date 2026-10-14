#!/bin/sh
lib="$1/mediatagger/lib-linux-aarch64-cp313"
rm -rf "$lib"
requirements=$(mktemp)
uv export --frozen --no-dev --no-hashes --no-emit-project > "$requirements"
uv pip install -q --python /usr/bin/python3.13 --target "$lib" -r "$requirements"
rm -f "$requirements"
python3.13 -m compileall -q --invalidation-mode unchecked-hash -x /deploy_lib/ "$lib"
debs="$1/mediatagger/debs"
mkdir -p "$debs"
cp "${APTPI:-$HOME/aptpi}"/var/cache/apt/archives/*.deb "$debs"
(cd "$debs" && apt-ftparchive packages . > Packages)
