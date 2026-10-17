from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage

from mediatagger.test_video import make_clip, wait_until_playing
from mediatagger.test_viewer import make_surface_ready, shown_viewer_on
from mediatagger.test_viewer_zoom import scroll, square_viewer_on


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


def test_after_pressing_r_on_an_image_moving_to_the_next_item_and_back_shows_it_unrotated_again(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    make_corner_marked_landscape(tmp_path / "IMG_2.png")
    viewer = square_viewer_on(qtbot, tmp_path)
    unrotated = viewer.grab().toImage()
    qtbot.keyClick(viewer, Qt.Key.Key_R)

    qtbot.keyClick(viewer, Qt.Key.Key_Right)
    qtbot.keyClick(viewer, Qt.Key.Key_Left)

    assert viewer.grab().toImage() == unrotated


def test_after_pressing_r_on_a_video_the_next_image_shows_unrotated(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4", duration=30)
    make_corner_marked_landscape(tmp_path / "IMG_2.png")
    viewer = square_viewer_on(qtbot, tmp_path)
    make_surface_ready(viewer)
    wait_until_playing(viewer.video_player.engine)
    qtbot.keyClick(viewer, Qt.Key.Key_R)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    frame = viewer.grab().toImage()  # unrotated 200x100 fitted 300x150 at y 75..224, its blue corner at x 0..29, y 75..104
    assert frame.pixelColor(15, 90) == QColor("blue")
    assert frame.pixelColor(285, 210) == QColor("red")


def test_pressing_r_on_an_image_leaves_its_file_bytes_and_modification_time_unchanged(qtbot, tmp_path):
    path = tmp_path / "IMG_1.png"
    make_corner_marked_landscape(path)
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    viewer = square_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_R)
    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_pressing_r_on_an_image_zoomed_in_one_notch_shows_it_turned_at_110_percent_of_its_turned_fitted_size(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    viewer = square_viewer_on(qtbot, tmp_path)
    scroll(viewer, 1, at=viewer.rect().center())

    qtbot.keyClick(viewer, Qt.Key.Key_R)

    frame = viewer.grab().toImage()  # turned fitted 150x300, at 110 % 165x330 centred: x 67.5..232.5
    assert [frame.pixelColor(x, 150) == QColor("black") for x in (65, 70, 230, 235)] == [True, False, False, True]


def test_zooming_in_on_a_turned_image_with_the_mouse_off_its_centre_keeps_the_picture_point_under_the_mouse(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    viewer = square_viewer_on(qtbot, tmp_path)
    qtbot.keyClick(viewer, Qt.Key.Key_R)  # turned 100x200 fitted 150x300 at x 75..224, its blue corner at x 195..224, y 0..29

    scroll(viewer, 1, at=QPoint(100, 50))

    frame = viewer.grab().toImage()  # 165x330 from (72.5, -5) keeps (100, 50) put: blue corner at x 204.5..237.5, y -5..28
    assert frame.pixelColor(220, 0) == QColor("blue")
    assert frame.pixelColor(220, 31) == QColor("red")
