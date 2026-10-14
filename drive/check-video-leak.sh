#!/bin/sh
# Run on the Pi: starts MediaTagger on a video and logs the app's open files every 10 s, to check that playback no longer
# leaks a sync_file per frame (Phase 9b). Results go to ~/mediatagger-check while the app runs, and are copied onto this
# drive's results/ only after the app has exited (the app's drive is never written while it runs).
# Usage: sh check-video-leak.sh [video-or-folder]   (default: the HEVC 1080p sample) — quit the app with Esc when done.
HERE=$(cd "$(dirname "$0")" && pwd)
TARGET=${1:-"$HERE/../samples/06_clip_hevc_1080p.mp4"}
STAMP=$(date +%Y-%m-%d-%H%M%S)
LOG="$HOME/mediatagger-check/$STAMP"
mkdir -p "$LOG"
{
  echo "app: $(cat "$HERE/app/VERSION")"
  echo "libmpv: $(dpkg-query -W -f='${Version}' libmpv2 2>/dev/null)"
  echo "session: ${XDG_SESSION_TYPE:-?} wayland=${WAYLAND_DISPLAY:-none}"
  echo "target: $TARGET"
  echo "fd limit: $(ulimit -n)"
} > "$LOG/info.txt"
cat "$LOG/info.txt"

sh "$HERE/run.sh" "$TARGET" > "$LOG/app.log" 2>&1 &
PID=$!
sleep 2
APP=$(pgrep -P "$PID" python3 || echo "$PID")  # run.sh execs python3, so this is normally $PID itself
echo "seconds total_fds sync_file_fds" | tee "$LOG/fds.txt"
START=$(date +%s)
while kill -0 "$APP" 2>/dev/null; do
  TOTAL=$(ls /proc/"$APP"/fd 2>/dev/null | wc -l)
  SYNC=$(ls -l /proc/"$APP"/fd 2>/dev/null | grep -c sync_file)
  echo "$(( $(date +%s) - START )) $TOTAL $SYNC" | tee -a "$LOG/fds.txt"
  sleep 10
done
wait "$PID"; echo "exit code: $?" >> "$LOG/info.txt"

OUT="$HERE/../results/check-video-leak-$STAMP"
mkdir -p "$OUT" && cp "$LOG"/* "$OUT/" && sync && echo "Results copied to $OUT"
