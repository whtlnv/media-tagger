#!/bin/sh
# Third video diagnostic (~4 min, hands off). Windows open and close by themselves.
#   sh /media/rb/MEDIATAGGER/mediatagger/diag-video3.sh
# Writes only to ~/diag-video3.txt; copy it to the stick afterwards.
HERE=$(cd "$(dirname "$0")" && pwd)
LOG=$HOME/diag-video3.txt
CLIP=$HERE/../samples/05_clip_h264_1080p.mp4
export PYTHONDONTWRITEBYTECODE=1
: > "$LOG"
for v in nested nested-fullscreen nested-overlay nested-overlay-fullscreen nested-sound; do
  echo "== $v" | tee -a "$LOG"
  PYTHONPATH="$HERE/lib-linux-aarch64-cp313" timeout 40 python3 "$HERE/diag-video3.py" "$v" "$CLIP" 2>"$HOME/diag-video3-$v.err" | tee -a "$LOG"
  echo "  errors: $(grep -v textinput "$HOME/diag-video3-$v.err" | sort -u | head -3 | tr '\n' ' ')" | tee -a "$LOG"
  sleep 2
done
# the real app (build on this stick), fullscreen as shipped and forced windowed
OUT=$HOME/diag-video3; rm -rf "$OUT"; mkdir -p "$OUT/xdg/data" "$OUT/xdg/config" "$OUT/xdg/cache"
for v in app-fullscreen app-windowed; do
  echo "== $v" | tee -a "$LOG"
  if [ "$v" = app-windowed ]; then patch='from PySide6.QtWidgets import QWidget; QWidget.setWindowState = lambda self, state: None; QWidget.showFullScreen = QWidget.show; '; else patch=''; fi
  XDG_DATA_HOME="$OUT/xdg/data" XDG_CONFIG_HOME="$OUT/xdg/config" XDG_CACHE_HOME="$OUT/xdg/cache" PYTHONPATH="$HERE/app:$HERE/lib-linux-aarch64-cp313" \
    python3 -c "${patch}import mediatagger; mediatagger.main()" "$CLIP" 2>"$HOME/diag-video3-$v.err" &
  pid=$!
  for t in 5 10 15 20 25; do
    sleep 5
    if kill -0 $pid 2>/dev/null; then echo "  t=${t}s sync_files=$(for f in /proc/$pid/fd/*; do readlink "$f"; done 2>/dev/null | grep -c sync_file)" | tee -a "$LOG"
    else echo "  t=${t}s APP EXITED" | tee -a "$LOG"; break; fi
  done
  kill $pid 2>/dev/null; sleep 2; kill -9 $pid 2>/dev/null
  echo "  errors: $(grep -v textinput "$HOME/diag-video3-$v.err" | sort -u | head -3 | tr '\n' ' ')" | tee -a "$LOG"
  sleep 2
done
echo "done — now run:  cp ~/diag-video3.txt /media/rb/MEDIATAGGER/results/" | tee -a "$LOG"
