from PySide6.QtCore import QSize

from mediatagger.test_viewer import make_image

from mediatagger.thumbnails import image_thumbnail


def test_a_wide_image_is_fitted_to_400_px_across_keeping_its_aspect_ratio(tmp_path):
    path = make_image(tmp_path / "wide.png", "red", width=1600, height=800)

    assert image_thumbnail(path).size() == QSize(400, 200)
