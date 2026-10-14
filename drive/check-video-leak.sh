#!/bin/sh
here=$(cd "$(dirname "$0")" && pwd -P)
stamp=$(date +%Y-%m-%d-%H%M%S)
log="$HOME/mediatagger-check/$stamp"
mkdir -p "$log"
{ cat "$here/app/VERSION"; echo "$1"; } > "$log/info.txt"
: > "$log/fds.txt"
sh "$here/run.sh" "$1" > "$log/app.log" 2>&1
mkdir -p "$here/../results"
cp -R "$log" "$here/../results/check-video-leak-$stamp"
