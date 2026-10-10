import shutil

import pytest
from PySide6.QtCore import QSize

from mediatagger.test_video import make_clip
from mediatagger.test_viewer import make_image, make_jpeg_tagged_rotate_90

from mediatagger.thumbnails import image_thumbnail, video_duration


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
