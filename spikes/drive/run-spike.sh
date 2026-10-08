#!/bin/sh
# Plays the test clips with the mpv-in-Qt spike, using the Python packages on this drive.
HERE=$(cd "$(dirname "$0")" && pwd)
export PYTHONPATH="$HERE/lib-linux-aarch64-cp313"
if [ $# -eq 0 ]; then set -- --check "$HERE"/testmedia/*; fi
exec python3 "$HERE/mpv_qt_embed.py" "$@"
