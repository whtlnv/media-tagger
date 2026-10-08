#!/bin/sh
# Run in the arm64 trixie VM: lays out the spike, Python packages and libmpv2 repo on the drive.
# Usage: sh build-drive.sh /media/me/MEDIATAGGER
set -e
DRIVE=${1:?usage: build-drive.sh <drive mount point>}
REPO=$(cd "$(dirname "$0")/../.." && pwd)
OUT="$DRIVE/mediatagger"
APTPI=${APTPI:-$HOME/aptpi}
mkdir -p "$OUT/debs" "$OUT/testmedia"

uv pip install -q --python /usr/bin/python3.13 --target "$OUT/lib-linux-aarch64-cp313" pyside6-essentials python-mpv
cp "$APTPI"/var/cache/apt/archives/*.deb "$OUT/debs/"
(cd "$OUT/debs" && apt-ftparchive packages . > Packages)
cp "$REPO/spikes/mpv_qt_embed.py" "$REPO/spikes/drive/setup-pi.sh" "$REPO/spikes/drive/run-spike.sh" "$OUT/"
cp "$HOME"/testmedia/* "$OUT/testmedia/"
sync
echo "Drive ready: $OUT"
