from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage

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
