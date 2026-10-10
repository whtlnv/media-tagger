import shutil
import subprocess
import time

import pytest
from PySide6.QtCore import QSize

from mediatagger.test_video import make_clip
from mediatagger.test_viewer import make_image, make_jpeg_tagged_rotate_90

from mediatagger.thumbnails import image_thumbnail, video_duration, video_thumbnail


def test_a_wide_image_is_fitted_to_400_px_across_keeping_its_aspect_ratio(tmp_path):
    path = make_image(tmp_path / "wide.png", "red", width=1600, height=800)

    assert image_thumbnail(path).size() == QSize(400, 200)


def test_a_tall_image_is_fitted_to_400_px_on_its_long_side(tmp_path):
    path = make_image(tmp_path / "tall.png", "red", width=300, height=600)

    assert image_thumbnail(path).size() == QSize(200, 400)


def test_an_image_tagged_rotated_90_is_thumbnailed_in_its_displayed_orientation(tmp_path):
    path = make_jpeg_tagged_rotate_90(tmp_path / "rotated.jpg", "red", width=1600, height=800)

    assert image_thumbnail(path).size() == QSize(200, 400)


def test_a_corrupt_image_yields_no_thumbnail(tmp_path):
    path = tmp_path / "corrupt.jpg"
    path.write_bytes(b"this is not a jpeg")

    assert image_thumbnail(path) is None


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_a_video_yields_its_duration_in_seconds(tmp_path):
    path = make_clip(tmp_path / "clip.mp4", duration=3)

    assert video_duration(path) == pytest.approx(3, abs=0.2)


def make_clip_turning_blue_after(path, red_seconds, duration):
    subprocess.run(
        ["ffmpeg", "-loglevel", "error",
         "-f", "lavfi", "-i", f"color=red:size=64x48:rate=10:duration={red_seconds}",
         "-f", "lavfi", "-i", f"color=blue:size=64x48:rate=10:duration={duration - red_seconds}",
         "-filter_complex", "[0][1]concat=n=2:v=1", "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )
    return path


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_a_videos_thumbnail_is_a_frame_from_about_10_percent_in_not_its_first_frame(tmp_path):
    path = make_clip_turning_blue_after(tmp_path / "clip.mp4", red_seconds=0.5, duration=10)

    frame = video_thumbnail(path)

    centre = frame.pixelColor(frame.width() // 2, frame.height() // 2)
    assert centre.blue() > 200 and centre.red() < 60


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_a_wide_videos_thumbnail_is_fitted_to_400_px_across_keeping_its_aspect_ratio(tmp_path):
    path = tmp_path / "wide.mp4"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error",
         "-f", "lavfi", "-i", "color=blue:size=1600x800:rate=10:duration=2",
         "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )

    assert video_thumbnail(path).size() == QSize(400, 200)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_without_ffmpeg_on_the_path_a_video_yields_no_thumbnail_and_no_duration(tmp_path, monkeypatch):
    path = make_clip(tmp_path / "clip.mp4", duration=3)
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))

    assert video_thumbnail(path) is None
    assert video_duration(path) is None


@pytest.mark.skipif(shutil.which("ffprobe") is None, reason="ffprobe is not installed")
def test_a_7_second_video_yields_a_duration_of_about_7_seconds(tmp_path):
    path = make_clip(tmp_path / "clip.mp4", duration=7)

    assert video_duration(path) == pytest.approx(7, abs=0.2)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_an_800_by_600_video_green_at_10_percent_yields_a_green_400_by_300_thumbnail(tmp_path):
    path = tmp_path / "clip.mp4"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error",
         "-f", "lavfi", "-i", "color=red:size=800x600:rate=10:duration=0.5",
         "-f", "lavfi", "-i", "color=green:size=800x600:rate=10:duration=9.5",
         "-filter_complex", "[0][1]concat=n=2:v=1", "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )

    frame = video_thumbnail(path)

    assert frame.size() == QSize(400, 300)
    centre = frame.pixelColor(frame.width() // 2, frame.height() // 2)
    assert centre.green() > 100 and centre.red() < 60 and centre.blue() < 60


def make_fake_tool(bin_dir, name, script):
    bin_dir.mkdir(exist_ok=True)
    tool = bin_dir / name
    tool.write_text("#!/bin/sh\n" + script + "\n")
    tool.chmod(0o755)
    return tool


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_when_ffmpeg_runs_past_its_timeout_a_video_yields_no_thumbnail_promptly(tmp_path, monkeypatch):
    path = make_clip(tmp_path / "clip.mp4", duration=3)
    make_fake_tool(tmp_path / "bin", "ffprobe", "echo 3.0")
    make_fake_tool(tmp_path / "bin", "ffmpeg", "exec /bin/sleep 30")
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))

    started = time.monotonic()
    thumbnail = video_thumbnail(path, timeout=0.5)

    assert thumbnail is None
    assert time.monotonic() - started < 5
