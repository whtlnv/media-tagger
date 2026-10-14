#!/bin/sh
here=$(cd "$(dirname "$0")" && pwd -P)
mkdir -p "$XDG_DATA_HOME/applications"
cat > "$XDG_DATA_HOME/applications/mediatagger.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=MediaTagger
Exec=sh "$here/run.sh"
Terminal=false
Categories=AudioVideo;Video;Graphics;
DESKTOP
dpkg-query -W libmpv2 >/dev/null 2>&1 && exit 0
work=$(mktemp -d)
printf 'deb [trusted=yes] file:%s/debs ./\n' "$here" > "$work/sources.list"
apt() {
  sudo apt-get -o Dir::Etc::sourcelist="$work/sources.list" -o Dir::Etc::sourceparts=- -o Dir::State::Lists="$work/lists" "$@"
}
apt update
apt install -y --no-install-recommends libmpv2
sudo rm -rf "$work"
