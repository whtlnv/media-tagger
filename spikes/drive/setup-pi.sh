#!/bin/sh
# One-time Pi setup, no network needed: installs libmpv2 from the package repo on this drive.
# apt only installs what the Pi is missing; packages it already has are left alone.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LISTS=$(mktemp -d)
mkdir -p "$LISTS/partial"
echo "deb [trusted=yes] file:$HERE/debs ./" > "$LISTS/drive.list"
APT="-o Dir::Etc::sourcelist=$LISTS/drive.list -o Dir::Etc::sourceparts=- -o Dir::State::Lists=$LISTS -o APT::Get::List-Cleanup=0"
sudo apt-get $APT update
sudo apt-get $APT install -y --no-install-recommends libmpv2
rm -rf "$LISTS"
echo "libmpv2 installed."
