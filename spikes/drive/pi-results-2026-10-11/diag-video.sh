#!/bin/sh
# Pi diagnostic for the "Too many open files" video crash. Run from a terminal, hands off the keyboard (~5 min):
#   sh /media/rb/MEDIATAGGER/mediatagger/diag-video.sh
# Plays one sample clip for 45 s under several settings and records how many files the app holds open.
# Writes only to ~/diag-video (never to this stick while the app runs); copy diag-video.txt to the stick afterwards.
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$HOME/diag-video; rm -rf "$OUT"; mkdir -p "$OUT/xdg/data" "$OUT/xdg/config" "$OUT/xdg/cache"
LOG=$OUT/diag-video.txt
CLIP=$HERE/../samples/05_clip_h264_1080p.mp4
{
  echo "== environment"; cat /proc/device-tree/model 2>/dev/null; echo
  echo "session=$XDG_SESSION_TYPE wayland=$WAYLAND_DISPLAY display=$DISPLAY ulimit-n=$(ulimit -n)"
  dpkg-query -W libmpv2 libegl-mesa0 libgl1-mesa-dri 2>/dev/null
  cat "$HERE/app/VERSION"
} > "$LOG"
run() {  # run <name> <python dict of extra mpv options> [env assignments...]
  name=$1; opts=$2; shift 2
  echo "== $name  (mpv options: $opts; env: $*)" | tee -a "$LOG"
  env "$@" XDG_DATA_HOME="$OUT/xdg/data" XDG_CONFIG_HOME="$OUT/xdg/config" XDG_CACHE_HOME="$OUT/xdg/cache" \
      PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$HERE/app:$HERE/lib-linux-aarch64-cp313" \
      python3 -c "import mediatagger.viewer as v; v._PLAYER_OPTIONS.update($opts); import mediatagger; mediatagger.main()" "$CLIP" \
      > "$OUT/$name.stderr" 2>&1 &
  pid=$!
  for t in 5 10 15 20 25 30 35 40 45; do
    sleep 5
    if kill -0 $pid 2>/dev/null; then echo "  t=${t}s open files=$(ls /proc/$pid/fd 2>/dev/null | wc -l)" >> "$LOG"
    else echo "  t=${t}s APP EXITED" >> "$LOG"; break; fi
  done
  if kill -0 $pid 2>/dev/null; then
    echo "  kinds of open files:" >> "$LOG"
    for f in /proc/$pid/fd/*; do readlink "$f"; done | sed -E 's/[0-9]+/N/g' | sort | uniq -c | sort -rn | head -8 >> "$LOG"
    kill $pid; sleep 2; kill -9 $pid 2>/dev/null
  fi
  echo "  messages:" >> "$LOG"
  grep -v textinput "$OUT/$name.stderr" | sed -E 's/0x[0-9a-f]+/0x_/g' | sort | uniq -c | sort -rn | head -6 >> "$LOG"
  sleep 2
}
run baseline        '{}'
run no-direct-render '{"vd_lavc_dr": "no"}'
run hwdec-drm       '{"hwdec": "drm"}'
run hwdec-drm-copy  '{"hwdec": "drm-copy"}'
run xwayland        '{}' QT_QPA_PLATFORM=xcb
echo "done — now run:  cp ~/diag-video/diag-video.txt /media/rb/MEDIATAGGER/results/" | tee -a "$LOG"
