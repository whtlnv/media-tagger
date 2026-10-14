#!/bin/sh
# One-time Pi setup, no network needed: installs libmpv2 from this drive's debs/ (apt only adds what the Pi lacks) and adds
# a "MediaTagger" menu entry that runs this drive's run.sh. Running it again is harmless.
# apt's "_apt ... Permission denied" notices are harmless (exFAT files aren't readable by apt's sandbox user).
# Usage: sh setup-pi.sh
here=$(cd "$(dirname "$0")" && pwd -P)
libmpv2_installed() {
  dpkg-query -W -f='${Status}' libmpv2 2>/dev/null | grep -q 'install ok installed'
}
install_libmpv2() {
  work=$(mktemp -d)
  mkdir -p "$work/lists/partial"
  printf 'deb [trusted=yes] file:%s/debs ./\n' "$here" > "$work/sources.list"
  apt() {
    sudo apt-get -o Dir::Etc::sourcelist="$work/sources.list" -o Dir::Etc::sourceparts=- -o Dir::State::Lists="$work/lists" "$@"
  }
  apt update
  apt install -y --no-install-recommends libmpv2 || return
  sudo rm -rf "$work"
}
libmpv2_installed || install_libmpv2 || exit
apps="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$apps"
cat > "$apps/mediatagger.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=MediaTagger
Exec=sh "$here/run.sh"
Terminal=false
Categories=AudioVideo;Video;
DESKTOP
echo "MediaTagger is in the menu (runs $here/run.sh)."
