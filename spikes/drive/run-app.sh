#!/bin/sh
# Runs MediaTagger from this drive with the Pi's own python3 and the packages stored next to it.
# Usage: sh run-app.sh [folder-or-file]
HERE=$(cd "$(dirname "$0")" && pwd)
export PYTHONPATH="$HERE/app:$HERE/lib-linux-aarch64-cp313"
exec python3 -c 'import mediatagger; mediatagger.main()' "$@"
