#!/bin/sh
# Run on the Mac: copies the current app code, its launcher and a sample folder onto the drive.
# Usage: sh spikes/drive/push-app.sh /Volumes/MEDIATAGGER
set -e
DRIVE=${1:?usage: push-app.sh <drive mount point>}
REPO=$(cd "$(dirname "$0")/../.." && pwd)
OUT="$DRIVE/mediatagger"
rm -rf "$OUT/app"
mkdir -p "$OUT/app/mediatagger"
for f in "$REPO"/src/mediatagger/*.py; do
  case "$(basename "$f")" in test_*|conftest.py) ;; *) cp -X "$f" "$OUT/app/mediatagger/" ;; esac
done
cp -X "$REPO/spikes/drive/run-app.sh" "$OUT/"
# Precompile app and packages (hash-based pycs that are never revalidated, not mtime-checked: exFAT timestamps are coarse) so the Pi never needs to write bytecode.
python3.13 -m compileall -q --invalidation-mode unchecked-hash "$OUT/app" "$OUT/lib-linux-aarch64-cp313" || echo "warning: precompile failed"
git -C "$REPO" log -1 --format='%h %s' > "$OUT/app/VERSION"
find "$DRIVE" -name '._*' -delete 2>/dev/null || true
sync
echo "App copied: $(cat "$OUT/app/VERSION")"
