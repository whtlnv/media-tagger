from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage

from mediatagger.test_viewer import shown_viewer_on
from mediatagger.test_viewer_zoom import square_viewer_on


def make_corner_marked_landscape(path):
    """A red 200x100 picture with a 20x20 blue square in its top-left corner."""
    picture = QImage(200, 100, QImage.Format.Format_RGB32)
    picture.fill(QColor("red"))
    for y in range(20):
        for x in range(20):
            picture.setPixelColor(x, y, QColor("blue"))
    picture.save(str(path))


def test_pressing_r_on_a_landscape_image_in_a_square_viewer_shows_it_turned_clockwise_drawn_whole_across_the_full_height(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    viewer = square_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_R)

    frame = viewer.grab().toImage()  # turned 100x200 fitted 150x300 at x 75..224, its blue corner at x 195..224, y 0..29
    assert frame.pixelColor(210, 15) == QColor("blue")
    assert frame.pixelColor(150, 2) == QColor("red")
    assert frame.pixelColor(150, 245) == QColor("red")  # clear of the status bar
    assert frame.pixelColor(60, 150) == QColor("black")
    assert frame.pixelColor(240, 150) == QColor("black")


def test_pressing_r_twice_on_an_image_shows_it_upside_down(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    viewer = square_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_R)
    qtbot.keyClick(viewer, Qt.Key.Key_R)

    frame = viewer.grab().toImage()  # upside down 200x100 fitted 300x150 at y 75..224, its blue corner at x 270..299, y 195..224
    assert frame.pixelColor(285, 210) == QColor("blue")
    assert frame.pixelColor(15, 90) == QColor("red")


def test_pressing_r_four_times_on_an_image_shows_it_exactly_as_it_was_fitted_before(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    viewer = square_viewer_on(qtbot, tmp_path)
    fitted = viewer.grab().toImage()

    for _ in range(4):
        qtbot.keyClick(viewer, Qt.Key.Key_R)

    assert viewer.grab().toImage() == fitted


def test_a_landscape_image_turned_once_in_a_wide_viewer_fills_its_height_centred_across_its_width(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.resize(600, 300)
    qtbot.waitUntil(lambda: viewer.width() == 600)

    qtbot.keyClick(viewer, Qt.Key.Key_R)

    frame = viewer.grab().toImage()  # turned 100x200 fitted 150x300 at x 225..374
    assert [frame.pixelColor(x, 150) == QColor("black") for x in (223, 227, 372, 376)] == [True, False, False, True]
    assert frame.pixelColor(300, 1) == QColor("red")


def test_after_pressing_r_on_an_image_the_next_image_shows_unrotated(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    make_corner_marked_landscape(tmp_path / "IMG_2.png")
    viewer = square_viewer_on(qtbot, tmp_path)
    unrotated = viewer.grab().toImage()
    qtbot.keyClick(viewer, Qt.Key.Key_R)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    assert viewer.grab().toImage() == unrotated
