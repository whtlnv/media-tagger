#!/bin/sh
here=$(cd "$(dirname "$0")" && pwd -P)
work=$(mktemp -d)
printf 'deb [trusted=yes] file:%s/debs ./\n' "$here" > "$work/sources.list"
apt() {
  sudo apt-get -o Dir::Etc::sourcelist="$work/sources.list" -o Dir::Etc::sourceparts=- -o Dir::State::Lists="$work/lists" "$@"
}
apt update
apt install -y --no-install-recommends libmpv2
