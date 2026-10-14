#!/bin/sh
here=$(cd "$(dirname "$0")" && pwd -P)
apps="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$apps"
cat > "$apps/mediatagger.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=MediaTagger
Exec=sh "$here/run.sh"
Terminal=false
Categories=AudioVideo;Video;Graphics;
DESKTOP
libmpv2_installed() {
  dpkg-query -W -f='${Status}' libmpv2 2>/dev/null | grep -q 'install ok installed'
}
libmpv2_installed && exit 0
work=$(mktemp -d)
printf 'deb [trusted=yes] file:%s/debs ./\n' "$here" > "$work/sources.list"
apt() {
  sudo apt-get -o Dir::Etc::sourcelist="$work/sources.list" -o Dir::Etc::sourceparts=- -o Dir::State::Lists="$work/lists" "$@"
}
apt update
apt install -y --no-install-recommends libmpv2
sudo rm -rf "$work"
