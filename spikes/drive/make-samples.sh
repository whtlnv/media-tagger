#!/bin/sh
# Run on the Mac: writes a folder of awkward sample media (big photo, sideways photo, AVI, MPG, H.264, HEVC 1080p and 4K, GIF, broken file).
# Usage: sh spikes/drive/make-samples.sh <output folder>
set -e
OUT=${1:?usage: make-samples.sh <output folder>}
mkdir -p "$OUT" && cd "$OUT"
q="-v error -y"
ffmpeg $q -f lavfi -i testsrc2=size=4000x3000 -frames:v 1 -q:v 3 01_photo_12mp.jpg
ffmpeg $q -f lavfi -i testsrc2=size=640x480:rate=25 -f lavfi -i sine=f=440 -t 10 -c:v mpeg4 -vtag XVID -c:a libmp3lame 03_clip_xvid.AVI
ffmpeg $q -f lavfi -i testsrc2=size=720x576:rate=25 -f lavfi -i sine=f=330 -t 10 -c:v mpeg2video -c:a mp2 04_clip_mpeg2.mpg
ffmpeg $q -f lavfi -i testsrc2=size=1920x1080:rate=30 -f lavfi -i sine=f=500 -t 10 -c:v libx264 -pix_fmt yuv420p -c:a aac 05_clip_h264_1080p.mp4
ffmpeg $q -f lavfi -i testsrc2=size=1920x1080:rate=30 -f lavfi -i sine=f=550 -t 10 -c:v libx265 -tag:v hvc1 -pix_fmt yuv420p -c:a aac 06_clip_hevc_1080p.mp4
ffmpeg $q -f lavfi -i testsrc2=size=3840x2160:rate=30 -f lavfi -i sine=f=600 -t 10 -c:v libx265 -tag:v hvc1 -pix_fmt yuv420p -c:a aac 07_clip_hevc_4k.mp4
ffmpeg $q -f lavfi -i testsrc2=size=320x240:rate=10 -t 3 08_anim.gif
printf 'not an image' > 09_broken.jpg
echo "not media" > notes.txt
ls -la
