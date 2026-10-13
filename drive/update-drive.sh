#!/bin/sh
here=$(cd "$(dirname "$0")" && pwd)
app="$1/mediatagger/app/mediatagger"
mkdir -p "$app"
cp "$here"/../src/mediatagger/*.py "$app"/
rm -f "$app"/test_*.py "$app"/conftest.py
