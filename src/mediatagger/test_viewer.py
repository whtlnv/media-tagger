import gc
import os
import struct
import subprocess
import sys
import threading
import weakref

import pytest
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QLabel

from mediatagger.test_video import make_clip

from mediatagger.mpv_surface import MpvSurface
from mediatagger.viewer import UNSUPPORTED_TEXT, Viewer, decode_fitted


def make_image(path, color, width=64, height=48):
    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor(color))
    image.save(str(path))
    return path


def make_folder_with_no_media(path):
    path.mkdir()
    (path / "notes.txt").write_text("hi")
    return path


def make_jpeg_tagged_rotate_90(path, color, width, height):
    """A JPEG stored as width x height whose EXIF orientation (6) says to show it rotated 90° clockwise."""
    make_image(path, color, width, height)
    tiff = b"MM\x00\x2a" + struct.pack(">IH", 8, 1) + struct.pack(">HHIHH", 0x0112, 3, 1, 6, 0) + struct.pack(">I", 0)
    exif = b"Exif\x00\x00" + tiff
    data = path.read_bytes()
    path.write_bytes(data[:2] + b"\xff\xe1" + struct.pack(">H", len(exif) + 2) + exif + data[2:])
    return path


SILENT = {"ao": "null"}


def offscreen_environment():
    return {**os.environ, "QT_QPA_PLATFORM": "offscreen"}


def run_python_offscreen(script, *arguments):
    return subprocess.run(
        [sys.executable, "-c", script, *arguments],
        capture_output=True, text=True, timeout=30,
        env=offscreen_environment(),
    )


def viewer_on(qtbot, folder):
    viewer = Viewer(folder, player_options=SILENT)
    qtbot.addWidget(viewer)
    return viewer


def unready_viewer_on(qtbot, folder):
    viewer = viewer_on(qtbot, folder)
    viewer.resize(400, 300)
    viewer.show()
    qtbot.waitExposed(viewer)
    return viewer


def shown_launch_viewer(qtbot, folder_picker=None):
    viewer = Viewer(player_options=SILENT, folder_picker=folder_picker)
    qtbot.addWidget(viewer)
    viewer.show()
    qtbot.waitExposed(viewer)
    return viewer


def make_surface_ready(viewer):
    """The offscreen platform has no OpenGL, so stand in for the video surface's render context being created."""
    surface = viewer.findChild(MpvSurface)
    if surface is not None:
        surface.became_ready()


def shown_viewer_on(qtbot, folder):
    viewer = unready_viewer_on(qtbot, folder)
    make_surface_ready(viewer)
    return viewer


def shown_labels(viewer):
    """Labels shown over the media area; the status bar's own labels are checked separately."""
    return [label for label in viewer.findChildren(QLabel) if label.isVisible() and not viewer.status_bar.isAncestorOf(label)]


def shown_texts(viewer):
    return [label.text() for label in shown_labels(viewer)]


def shows_unsupported_placeholder(viewer):
    return any("unsupported" in text.lower() for text in shown_texts(viewer))


def shows_video_surface(viewer):
    surface = viewer.findChild(QOpenGLWidget)
    return surface is not None and surface.isVisible()


def wait_until_loaded(engine, clip):
    engine.wait_for_property("path", lambda path: path == str(clip), timeout=5)


def centre_colour(viewer):
    frame = viewer.grab().toImage()
    return frame.pixelColor(frame.width() // 2, frame.height() // 2)


def centre_colour_of_viewer_on(qtbot, folder):
    return centre_colour(shown_viewer_on(qtbot, folder))


def test_a_viewer_opened_on_a_folder_whose_first_item_is_red_paints_red_at_its_centre(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    assert centre_colour_of_viewer_on(qtbot, tmp_path) == QColor("red")


def test_a_viewer_opened_on_a_folder_whose_first_item_is_blue_paints_blue_at_its_centre(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "blue")
    make_image(tmp_path / "IMG_2.png", "red")
    assert centre_colour_of_viewer_on(qtbot, tmp_path) == QColor("blue")


def test_pressing_right_in_the_viewer_on_a_red_image_followed_by_a_blue_image_paints_blue_and_left_paints_red_again(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_Right)
    assert centre_colour(viewer) == QColor("blue")

    qtbot.keyClick(viewer, Qt.Key.Key_Left)
    assert centre_colour(viewer) == QColor("red")


def test_a_viewer_draws_a_wide_red_image_fitted_to_a_square_window_with_black_above_and_below_it(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red", width=200, height=100)
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.resize(300, 300)
    qtbot.waitUntil(lambda: viewer.size().width() == viewer.size().height())

    frame = viewer.grab().toImage()
    middle = frame.width() // 2
    assert frame.pixelColor(middle, frame.height() // 2) == QColor("red")
    assert frame.pixelColor(middle, 10) == QColor("black")
    assert frame.pixelColor(middle, frame.height() - 10) == QColor("black")


def test_pressing_i_in_the_viewer_draws_the_info_overlay_over_the_shown_image_and_pressing_i_again_removes_it(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)
    plain = viewer.grab().toImage()

    qtbot.keyClick(viewer, Qt.Key.Key_I)
    with_overlay = viewer.grab().toImage()
    assert with_overlay != plain

    qtbot.keyClick(viewer, Qt.Key.Key_I)
    assert viewer.grab().toImage() == plain


def test_the_viewers_i_overlay_is_corner_text_with_the_filename_and_position_that_follows_space_and_leaves_the_image_visible(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_viewer_on(qtbot, tmp_path)
    half_width, half_height = viewer.width() // 2, viewer.height() // 2
    corners = [QRect(x, y, half_width, half_height) for x in (0, half_width) for y in (0, half_height)]

    def shown_overlay_and_centre_colour():
        labels = shown_labels(viewer)
        assert len(labels) == 1
        assert any(corner.contains(labels[0].geometry()) for corner in corners)
        return labels[0].text(), centre_colour(viewer)

    qtbot.keyClick(viewer, Qt.Key.Key_I)
    text, centre = shown_overlay_and_centre_colour()
    assert "IMG_1.png" in text and "1 / 2" in text
    assert centre == QColor("red")

    qtbot.keyClick(viewer, Qt.Key.Key_Space)
    text, centre = shown_overlay_and_centre_colour()
    assert "IMG_2.png" in text and "2 / 2" in text
    assert centre == QColor("blue")


@pytest.mark.parametrize("presses, fullscreen", [
    pytest.param(0, True, id="a viewer opened on a folder and shown is fullscreen"),
    pytest.param(1, False, id="f in the fullscreen viewer leaves fullscreen"),
    pytest.param(2, True, id="f when the viewer is not fullscreen enters fullscreen"),
])
def test_a_shown_viewer_opens_fullscreen_and_each_f_press_toggles_it(qtbot, tmp_path, presses, fullscreen):
    make_image(tmp_path / "IMG_1.png", "red")
    viewer = viewer_on(qtbot, tmp_path)
    viewer.show()
    qtbot.waitExposed(viewer)

    for _ in range(presses):
        qtbot.keyClick(viewer, Qt.Key.Key_F)

    assert viewer.isFullScreen() is fullscreen


def test_a_viewer_opened_on_a_folder_whose_first_item_cannot_be_decoded_shows_an_unsupported_placeholder(qtbot, tmp_path):
    (tmp_path / "IMG_1.png").write_bytes(b"not really a png")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)

    assert shown_texts(viewer) == [UNSUPPORTED_TEXT]


def test_a_viewer_opened_on_a_folder_whose_first_item_is_a_decodable_image_shows_that_image_and_no_unsupported_placeholder(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    (tmp_path / "IMG_2.png").write_bytes(b"not really a png")
    viewer = shown_viewer_on(qtbot, tmp_path)

    assert not shows_unsupported_placeholder(viewer)
    assert centre_colour(viewer) == QColor("red")


def test_pressing_space_in_the_viewer_on_an_unsupported_placeholder_followed_by_a_red_image_hides_the_placeholder_and_paints_red(qtbot, tmp_path):
    (tmp_path / "IMG_1.png").write_bytes(b"not really a png")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    assert not shows_unsupported_placeholder(viewer)
    assert centre_colour(viewer) == QColor("red")


def test_pressing_a_key_the_viewer_does_not_use_on_a_red_image_followed_by_a_blue_image_keeps_painting_red(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_X)

    assert centre_colour(viewer) == QColor("red")


def test_the_unsupported_placeholder_sits_at_the_centre_of_the_window_and_stays_there_on_resize(qtbot, tmp_path):
    (tmp_path / "IMG_1.png").write_bytes(b"not really a png")
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.resize(600, 500)
    qtbot.waitUntil(lambda: viewer.width() == 600)

    offset = viewer.placeholder.geometry().center() - viewer.rect().center()
    assert offset.manhattanLength() <= 2


def light_theme(viewer):
    """A desktop theme like the Pi's, whose default text colour is black."""
    palette = viewer.palette()
    palette.setColor(palette.ColorRole.WindowText, QColor("black"))
    viewer.setPalette(palette)


def colours_inside(viewer, label):
    frame = viewer.grab().toImage()
    area = label.geometry()
    return [frame.pixelColor(x, y) for x in range(area.left(), area.right()) for y in range(area.top(), area.bottom())]


def test_the_info_overlay_is_light_text_on_a_dark_translucent_panel_whatever_the_desktop_theme(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red", width=400, height=300)
    viewer = shown_viewer_on(qtbot, tmp_path)
    light_theme(viewer)

    qtbot.keyClick(viewer, Qt.Key.Key_I)

    colours = colours_inside(viewer, viewer.info)
    assert any(colour.lightness() > 200 and colour.saturation() < 40 for colour in colours)  # light text
    frame = viewer.grab().toImage()
    panel = frame.pixelColor(viewer.info.geometry().left() + 4, viewer.info.geometry().center().y())  # in the padding
    assert panel != QColor("red") and panel.red() < 200 and panel.red() > 0  # red image dimmed, not hidden


def test_the_unsupported_placeholder_is_light_text_whatever_the_desktop_theme(qtbot, tmp_path):
    (tmp_path / "IMG_1.png").write_bytes(b"not really a png")
    viewer = shown_viewer_on(qtbot, tmp_path)
    light_theme(viewer)

    colours = colours_inside(viewer, viewer.placeholder)
    assert any(colour.lightness() > 200 and colour.saturation() < 40 for colour in colours)


def test_a_viewer_opened_on_a_folder_with_no_media_says_so_at_the_centre_and_ignores_keys(qtbot, tmp_path):
    folder = make_folder_with_no_media(tmp_path / "Holidays")
    viewer = shown_viewer_on(qtbot, folder)

    for key in (Qt.Key.Key_Space, Qt.Key.Key_Left, Qt.Key.Key_I, Qt.Key.Key_P):
        qtbot.keyClick(viewer, key)

    shown = shown_labels(viewer)
    assert [label.text() for label in shown] == ["No images or videos in Holidays"]
    assert (shown[0].geometry().center() - viewer.rect().center()).manhattanLength() <= 2


def test_an_image_larger_than_the_window_is_decoded_at_most_at_the_window_size_keeping_its_shape(tmp_path):
    make_image(tmp_path / "IMG_1.jpg", "red", width=4000, height=3000)

    decoded = decode_fitted(tmp_path / "IMG_1.jpg", QSize(400, 400))

    assert decoded.size() == QSize(400, 300)


def test_a_jpeg_smaller_than_the_window_tagged_rotate_90_is_drawn_upright_taller_than_wide(qtbot, tmp_path):
    make_jpeg_tagged_rotate_90(tmp_path / "IMG_1.jpg", "red", width=200, height=100)
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.resize(300, 300)
    qtbot.waitUntil(lambda: viewer.size().width() == viewer.size().height())

    frame = viewer.grab().toImage()
    middle_x, middle_y = frame.width() // 2, frame.height() // 2
    photo = frame.pixelColor(middle_x, middle_y)  # JPEG decodes red as near-red, so compare against the drawn photo
    assert photo != QColor("black")
    assert frame.pixelColor(middle_x, middle_y - 80) == photo
    assert frame.pixelColor(middle_x - 80, middle_y) == QColor("black")


def test_a_jpeg_larger_than_the_window_tagged_rotate_90_is_decoded_upright_fitted_to_the_window(tmp_path):
    make_jpeg_tagged_rotate_90(tmp_path / "IMG_1.jpg", "red", width=800, height=400)

    decoded = decode_fitted(tmp_path / "IMG_1.jpg", QSize(400, 300))

    assert decoded.size() == QSize(150, 300)


def test_the_viewer_decodes_the_shown_image_once_however_often_it_repaints(qtbot, tmp_path, monkeypatch):
    make_image(tmp_path / "IMG_1.png", "red")
    decodes = []

    def counted_decode_fitted(path, bounds):
        decodes.append((path, bounds))
        return decode_fitted(path, bounds)

    monkeypatch.setattr("mediatagger.viewer.decode_fitted", counted_decode_fitted)
    viewer = shown_viewer_on(qtbot, tmp_path)
    assert decodes and all(path == tmp_path / "IMG_1.png" for path, _ in decodes)
    decodes.clear()

    for _ in range(3):
        viewer.repaint()

    assert decodes == []
    assert centre_colour(viewer) == QColor("red")


def test_pressing_esc_closes_the_viewer_and_shuts_down_its_video_player(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)
    engine = viewer.video_player.engine
    wait_until_loaded(engine, clip)

    qtbot.keyClick(viewer, Qt.Key.Key_Escape)

    assert not viewer.isVisible()
    assert engine.handle is None


def test_a_slideshow_shows_a_status_bar_across_the_bottom_edge_of_the_window_over_an_image_that_still_fills_the_window(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)

    bar = viewer.childAt(viewer.width() // 2, viewer.height() - 2)
    assert bar is not None and bar.isVisible()
    assert bar.geometry().left() == 0 and bar.geometry().right() == viewer.rect().right()
    assert bar.geometry().bottom() == viewer.rect().bottom()
    assert bar.height() < viewer.height() // 4
    assert centre_colour(viewer) == QColor("red")


def test_once_a_viewer_exists_garbage_is_collected_on_the_gui_thread_never_on_a_background_thread_such_as_mpvs_event_thread(qtbot):
    """A widget freed by the garbage collector on another thread is destroyed there while the GUI thread may be painting it."""
    viewer = Viewer(player_options=SILENT)
    qtbot.addWidget(viewer)
    collected_on = []

    class Cycle:
        pass

    garbage = Cycle()
    garbage.itself = garbage
    weakref.finalize(garbage, lambda: collected_on.append(threading.current_thread()))
    del garbage
    busy = threading.Thread(target=lambda: [[] for _ in range(100_000)])  # enough allocations to trigger a collection
    busy.start()
    busy.join()
    qtbot.waitUntil(lambda: bool(collected_on))

    assert collected_on == [threading.main_thread()]
