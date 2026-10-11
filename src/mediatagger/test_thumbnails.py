import shutil
import subprocess
import time

import pytest
from PySide6.QtCore import QSize

from mediatagger.test_video import make_clip
from mediatagger.test_viewer import make_image, make_jpeg_tagged_rotate_90

from mediatagger.thumbnails import folder_thumbnail, format_duration, image_thumbnail, video_duration, video_thumbnail


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


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_when_ffprobe_runs_past_its_timeout_a_video_yields_no_duration_and_no_thumbnail_promptly(tmp_path, monkeypatch):
    path = make_clip(tmp_path / "clip.mp4", duration=3)
    make_fake_tool(tmp_path / "bin", "ffprobe", "exec /bin/sleep 30")
    make_fake_tool(tmp_path / "bin", "ffmpeg", "exit 1")
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))

    started = time.monotonic()
    duration = video_duration(path, timeout=0.5)
    thumbnail = video_thumbnail(path, timeout=0.5)

    assert duration is None
    assert thumbnail is None
    assert time.monotonic() - started < 5


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_a_corrupt_video_yields_no_thumbnail_and_no_duration(tmp_path):
    path = tmp_path / "corrupt.mp4"
    path.write_bytes(b"this is not an mp4")

    assert video_thumbnail(path) is None
    assert video_duration(path) is None


def test_a_folder_holding_10_jpg_and_2_jpg_yields_the_thumbnail_of_2_jpg_first_in_natural_order(tmp_path):
    folder = tmp_path / "album"
    folder.mkdir()
    make_image(folder / "10.jpg", "red", width=400, height=800)
    make_image(folder / "2.jpg", "green", width=800, height=400)

    thumbnail = folder_thumbnail(folder)

    assert thumbnail.size() == QSize(400, 200)
    centre = thumbnail.pixelColor(thumbnail.width() // 2, thumbnail.height() // 2)
    assert centre.green() > 100 and centre.red() < 60


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_a_folder_holding_only_a_gif_video_and_a_subfolder_with_an_image_yields_no_thumbnail(tmp_path):
    folder = tmp_path / "album"
    folder.mkdir()
    subprocess.run(
        ["ffmpeg", "-loglevel", "error",
         "-f", "lavfi", "-i", "color=red:size=64x48:rate=10:duration=1", str(folder / "clip.gif")],
        check=True,
    )
    (folder / "sub").mkdir()
    make_image(folder / "sub" / "photo.jpg", "green")

    assert folder_thumbnail(folder) is None


@pytest.mark.parametrize("seconds, text", [
    pytest.param(75, "1:15", id="75 seconds reads 1:15"),
    pytest.param(3725, "1:02:05", id="3725 seconds reads 1:02:05 with hours shown"),
    pytest.param(75.6, "1:15", id="a fractional 75.6 seconds reads 1:15 in whole seconds"),
])
def test_a_duration_reads_as_minutes_and_seconds(seconds, text):
    assert format_duration(seconds) == text


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_a_tiles_video_generation_with_no_timeout_given_still_gives_up_on_a_hung_ffmpeg(tmp_path, monkeypatch):
    from mediatagger import thumbnails

    path = make_clip(tmp_path / "clip.mp4", duration=3)
    make_fake_tool(tmp_path / "bin", "ffprobe", "exec /bin/sleep 30")
    make_fake_tool(tmp_path / "bin", "ffmpeg", "exec /bin/sleep 30")
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))
    monkeypatch.setattr(thumbnails, "TOOL_TIMEOUT_S", 0.5)

    started = time.monotonic()
    generated = thumbnails.thumbnail_and_duration(path)

    assert (generated, time.monotonic() - started < 5) == ((None, None), True)


def test_a_video_whose_frame_ffmpeg_cannot_extract_yields_no_thumbnail(tmp_path, monkeypatch):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"a video ffmpeg chokes on")
    make_fake_tool(tmp_path / "bin", "ffprobe", "echo 3.0")
    make_fake_tool(tmp_path / "bin", "ffmpeg", "exit 1")
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))

    assert video_thumbnail(path) is None


def test_a_video_whose_duration_ffprobe_reports_as_not_available_yields_no_duration(tmp_path, monkeypatch):
    path = tmp_path / "stream.mp4"
    path.write_bytes(b"a video with no duration")
    make_fake_tool(tmp_path / "bin", "ffprobe", "echo N/A")
    make_fake_tool(tmp_path / "bin", "ffmpeg", "exit 1")
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))

    assert video_duration(path) is None


def test_with_ffmpeg_but_no_ffprobe_on_the_path_a_video_yields_no_duration_and_no_thumbnail(tmp_path, monkeypatch):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"a video")
    make_fake_tool(tmp_path / "bin", "ffmpeg", "exit 1")
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))

    assert (video_duration(path), video_thumbnail(path)) == (None, None)
