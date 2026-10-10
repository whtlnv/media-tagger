from PySide6.QtCore import QSize

from mediatagger.test_viewer import make_image, make_jpeg_tagged_rotate_90

from mediatagger.thumbnails import image_thumbnail


def test_a_wide_image_is_fitted_to_400_px_across_keeping_its_aspect_ratio(tmp_path):
    path = make_image(tmp_path / "wide.png", "red", width=1600, height=800)

    assert image_thumbnail(path).size() == QSize(400, 200)


def test_a_tall_image_is_fitted_to_400_px_on_its_long_side(tmp_path):
    path = make_image(tmp_path / "tall.png", "red", width=300, height=600)

    assert image_thumbnail(path).size() == QSize(200, 400)


def test_an_image_tagged_rotated_90_is_thumbnailed_in_its_displayed_orientation(tmp_path):
    path = make_jpeg_tagged_rotate_90(tmp_path / "rotated.jpg", "red", width=1600, height=800)

    assert image_thumbnail(path).size() == QSize(200, 400)
