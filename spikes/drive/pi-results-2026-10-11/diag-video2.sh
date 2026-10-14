#!/bin/sh
# Second video diagnostic (~3 min, hands off). Windows open and close by themselves.
#   sh /media/rb/MEDIATAGGER/mediatagger/diag-video2.sh
# Writes only to ~/diag-video2.txt; copy it to the stick afterwards.
HERE=$(cd "$(dirname "$0")" && pwd)
LOG=$HOME/diag-video2.txt
CLIP=$HERE/../samples/05_clip_h264_1080p.mp4
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$HERE/lib-linux-aarch64-cp313"
: > "$LOG"
for v in qt-widget-only qt-window-only mpv-standalone mpv-in-qt-widget mpv-in-qt-window mpv-wid-xcb; do
  echo "== $v" | tee -a "$LOG"
  if [ "$v" = mpv-wid-xcb ]; then plat=xcb; else plat=wayland; fi
  QT_QPA_PLATFORM=$plat timeout 40 python3 "$HERE/diag-video2.py" "$v" "$CLIP" 2>"$HOME/diag-video2-$v.err" | tee -a "$LOG"
  echo "  exit=$?  errors: $(grep -v textinput "$HOME/diag-video2-$v.err" | sort -u | head -3 | tr '\n' ' ')" | tee -a "$LOG"
  sleep 2
done
echo "done — now run:  cp ~/diag-video2.txt /media/rb/MEDIATAGGER/results/" | tee -a "$LOG"
