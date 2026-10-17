from PySide6.QtCore import QPoint, Qt

from mediatagger.test_viewer import make_image
from mediatagger.test_viewer_turn import make_corner_marked_landscape
from mediatagger.test_viewer_zoom import scroll, square_viewer_on


def test_pressing_0_on_a_photo_zoomed_in_off_its_centre_shows_it_exactly_as_it_was_first_fitted(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red", width=200, height=100)
    viewer = square_viewer_on(qtbot, tmp_path)
    fitted = viewer.grab().toImage()
    scroll(viewer, 3, at=QPoint(60, 100))

    qtbot.keyClick(viewer, Qt.Key.Key_0)

    assert viewer.grab().toImage() == fitted


def test_pressing_0_on_a_photo_turned_once_shows_it_exactly_as_it_was_first_fitted_unturned(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    viewer = square_viewer_on(qtbot, tmp_path)
    fitted = viewer.grab().toImage()
    qtbot.keyClick(viewer, Qt.Key.Key_R)

    qtbot.keyClick(viewer, Qt.Key.Key_0)

    assert viewer.grab().toImage() == fitted
