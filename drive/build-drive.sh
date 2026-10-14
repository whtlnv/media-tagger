#!/bin/sh
requirements=$(mktemp)
uv export --frozen --no-dev --no-hashes --no-emit-project > "$requirements"
uv pip install -q --python /usr/bin/python3.13 --target "$1/mediatagger/lib-linux-aarch64-cp313" -r "$requirements"
rm -f "$requirements"
