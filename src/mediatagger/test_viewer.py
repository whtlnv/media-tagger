from PySide6.QtGui import QColor, QImage

from mediatagger.viewer import Viewer


def make_image(path, color):
    image = QImage(64, 48, QImage.Format.Format_RGB32)
    image.fill(QColor(color))
    image.save(str(path))
    return path


def test_a_viewer_opened_on_a_folder_whose_first_item_is_red_paints_red_at_its_centre(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = Viewer(tmp_path)
    qtbot.addWidget(viewer)
    viewer.resize(400, 300)
    viewer.show()
    qtbot.waitExposed(viewer)

    frame = viewer.grab().toImage()

    assert frame.pixelColor(frame.width() // 2, frame.height() // 2) == QColor("red")
