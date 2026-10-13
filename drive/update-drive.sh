#!/bin/sh
here=$(cd "$(dirname "$0")" && pwd)
app="$1/mediatagger/app/mediatagger"
rm -rf "$app"
mkdir -p "$app"
cp "$here"/../src/mediatagger/*.py "$app"/
rm -f "$app"/test_*.py "$app"/conftest.py
python3.13 -m compileall -q --invalidation-mode unchecked-hash "$app"
version="$1/mediatagger/app/VERSION"
git -C "$here/.." log -1 --format="%h %s" > "$version" || echo unknown > "$version"
