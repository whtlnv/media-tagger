import os
import subprocess
import sys

import pytest
from PySide6.QtCore import QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QImage
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QApplication, QFileDialog, QLabel

from mediatagger.test_video import make_clip, wait_until_playing

from mediatagger.mpv_surface import MpvSurface
from mediatagger.viewer import Viewer, decode_fitted


def make_image(path, color, width=64, height=48):
    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor(color))
    image.save(str(path))
    return path


SILENT = {"ao": "null"}


def offscreen_environment():
    return {**os.environ, "QT_QPA_PLATFORM": "offscreen"}


def run_python_offscreen(script, argument):
    return subprocess.run(
        [sys.executable, "-c", script, argument],
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


def shown_launch_viewer(qtbot):
    viewer = Viewer(player_options=SILENT)
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
    return [label for label in viewer.findChildren(QLabel) if label.isVisible()]


def shown_texts(viewer):
    return [label.text() for label in shown_labels(viewer)]


def modal_opened_by_key(qtbot, viewer, key):
    modals = []

    def close_whatever_is_open():
        modal = QApplication.activeModalWidget()
        modals.append(modal)
        if modal is not None:
            modal.reject()

    QTimer.singleShot(200, close_whatever_is_open)
    qtbot.keyClick(viewer, key)
    qtbot.waitUntil(lambda: len(modals) == 1)
    return modals[0]


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


def test_a_viewer_opened_on_a_folder_whose_first_item_is_a_video_shows_a_video_surface_loaded_with_that_clip(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)

    surface = viewer.findChild(QOpenGLWidget)
    assert surface is not None and surface.isVisible()
    assert viewer.rect().contains(surface.geometry())
    wait_until_loaded(viewer.video_player.engine, clip)


def test_a_viewer_opened_on_a_folder_whose_first_item_is_an_image_shows_no_video_surface_and_loads_no_clip(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_clip(tmp_path / "IMG_2.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)

    assert not shows_video_surface(viewer)
    assert viewer.video_player.engine.path is None


def test_pressing_space_in_the_viewer_on_a_video_followed_by_a_red_image_hides_the_video_surface_and_paints_red(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    assert not shows_video_surface(viewer)
    assert centre_colour(viewer) == QColor("red")


def test_pressing_space_in_the_viewer_on_a_video_followed_by_an_image_leaves_the_player_stopped(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)
    wait_until_loaded(viewer.video_player.engine, clip)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    assert viewer.video_player.engine.path is None


def test_the_viewers_video_player_renders_through_libmpv_into_the_surface_and_plays_sound_on_the_default_audio_output(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    viewer = Viewer(tmp_path)
    qtbot.addWidget(viewer)

    engine = viewer.video_player.engine
    assert [output["name"] for output in engine.vo] == ["libmpv"]
    assert "null" not in [output["name"] for output in engine.ao]


def test_pressing_m_in_the_viewer_on_a_video_mutes_the_video_player(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)
    wait_until_loaded(viewer.video_player.engine, clip)

    qtbot.keyClick(viewer, Qt.Key.Key_M)

    assert viewer.video_player.engine.mute is True


def test_pressing_right_in_the_viewer_on_a_red_image_followed_by_a_blue_image_paints_blue_and_left_paints_red_again(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_Right)
    assert centre_colour(viewer) == QColor("blue")

    qtbot.keyClick(viewer, Qt.Key.Key_Left)
    assert centre_colour(viewer) == QColor("red")


def test_pressing_space_in_the_viewer_on_an_image_followed_by_a_video_shows_the_video_surface_and_plays_that_clip(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    clip = make_clip(tmp_path / "IMG_2.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)
    make_surface_ready(viewer)

    assert shows_video_surface(viewer)
    wait_until_loaded(viewer.video_player.engine, clip)


def test_pressing_p_in_the_viewer_on_a_video_pauses_it_and_up_seeks_it_forward(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4", duration=30)
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)
    engine = viewer.video_player.engine
    wait_until_playing(engine)

    qtbot.keyClick(viewer, Qt.Key.Key_P)
    assert engine.pause is True

    before = engine.time_pos
    qtbot.keyClick(viewer, Qt.Key.Key_Up)
    assert engine.time_pos == pytest.approx(before + 10, abs=1)


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


def test_a_viewer_created_while_the_numeric_locale_is_not_c_still_gets_a_working_player(tmp_path):
    """QApplication sets LC_NUMERIC from the environment; libmpv refuses to start (and python-mpv crashes) unless it is "C"."""
    make_image(tmp_path / "IMG_1.png", "red")
    script = (
        "import locale, sys\n"
        "from pathlib import Path\n"
        "from PySide6.QtWidgets import QApplication\n"
        "from mediatagger.viewer import Viewer\n"
        "app = QApplication([])\n"
        "locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')\n"
        "viewer = Viewer(Path(sys.argv[1]))\n"
        "print(viewer.video_player.engine.path)\n"
        "viewer.close()\n"
    )
    result = run_python_offscreen(script, str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "None"


def test_a_viewer_given_null_audio_player_options_plays_its_video_silently_but_still_through_libmpv(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4")
    viewer = Viewer(tmp_path, player_options=SILENT)
    qtbot.addWidget(viewer)

    engine = viewer.video_player.engine
    assert [output["name"] for output in engine.ao] == ["null"]
    assert [output["name"] for output in engine.vo] == ["libmpv"]


def test_closing_the_viewer_shuts_down_its_video_player(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)
    engine = viewer.video_player.engine
    wait_until_loaded(engine, clip)

    viewer.close()

    assert engine.handle is None


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

    assert shows_unsupported_placeholder(viewer)


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


def test_a_viewer_opened_on_a_folder_whose_first_item_is_a_video_fills_its_window_with_the_video_surface_and_shows_no_unsupported_placeholder(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)

    assert not shows_unsupported_placeholder(viewer)
    assert viewer.findChild(QOpenGLWidget).geometry() == viewer.rect()


def test_a_viewer_opened_on_a_folder_whose_first_item_is_a_corrupt_video_shows_the_unsupported_placeholder_instead_of_a_video_surface(qtbot, tmp_path):
    (tmp_path / "IMG_1.mp4").write_bytes(b"not really an mp4")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.waitUntil(lambda: shows_unsupported_placeholder(viewer), timeout=5000)
    assert not shows_video_surface(viewer)


def test_pressing_a_key_the_viewer_does_not_use_on_a_red_image_followed_by_a_blue_image_keeps_painting_red(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_X)

    assert centre_colour(viewer) == QColor("red")


def test_pressing_down_in_the_viewer_on_a_paused_video_seeks_it_ten_seconds_back(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4", duration=30)
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)
    engine = viewer.video_player.engine
    wait_until_playing(engine)
    qtbot.keyClick(viewer, Qt.Key.Key_P)
    engine.time_pos = 20
    engine.wait_for_property("time-pos", lambda time_pos: time_pos == pytest.approx(20, abs=1), timeout=5)

    qtbot.keyClick(viewer, Qt.Key.Key_Down)

    assert engine.time_pos == pytest.approx(10, abs=1)


def test_pressing_enter_in_the_viewer_on_a_video_toggles_its_pause(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4", duration=30)
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)
    engine = viewer.video_player.engine
    wait_until_playing(engine)

    qtbot.keyClick(viewer, Qt.Key.Key_Return)
    assert engine.pause is True

    qtbot.keyClick(viewer, Qt.Key.Key_Return)
    assert engine.pause is False


def test_the_viewers_video_surface_renders_the_viewers_own_player(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)
    wait_until_loaded(viewer.video_player.engine, clip)

    surface = viewer.findChild(MpvSurface)
    assert surface is not None and surface.isVisible()
    assert surface.engine is viewer.video_player.engine


def test_a_video_reached_from_an_image_fills_the_viewer_window(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_clip(tmp_path / "IMG_2.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    assert viewer.findChild(MpvSurface).geometry() == viewer.rect()


def test_the_info_overlay_stays_on_top_of_a_video(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_clip(tmp_path / "IMG_2.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_I)
    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    assert viewer.childAt(viewer.info.geometry().center()) is viewer.info


def test_a_video_shown_before_its_surface_can_render_is_loaded_exactly_once_when_the_surface_becomes_ready(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    viewer = unready_viewer_on(qtbot, tmp_path)
    engine = viewer.video_player.engine
    loads = []
    engine.event_callback("start_file")(lambda event: loads.append(event))
    assert engine.path is None  # nothing loads before the surface can render, or mpv drops the clip's video

    viewer.findChild(MpvSurface).became_ready()

    wait_until_loaded(engine, clip)
    qtbot.wait(300)
    assert len(loads) == 1


def test_leaving_a_video_before_its_surface_can_render_never_loads_it(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = unready_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)
    viewer.findChild(MpvSurface).became_ready()

    qtbot.wait(300)
    assert viewer.video_player.engine.path is None


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
    folder = tmp_path / "Holidays"
    folder.mkdir()
    (folder / "notes.txt").write_text("hi")
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


def test_a_viewer_opened_with_no_path_shows_only_the_launch_text(qtbot):
    viewer = shown_launch_viewer(qtbot)

    assert shown_texts(viewer) == ["Drop a folder or file here, or press `o` to open"]


def test_a_viewer_opened_on_a_folder_shows_its_first_item_and_not_the_launch_text(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_viewer_on(qtbot, tmp_path)

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("red")


def test_pressing_o_on_the_launch_screen_opens_a_folder_picker(qtbot):
    viewer = shown_launch_viewer(qtbot)

    picker = modal_opened_by_key(qtbot, viewer, Qt.Key.Key_O)

    assert isinstance(picker, QFileDialog)
    assert picker.fileMode() == QFileDialog.FileMode.Directory


def test_pressing_a_key_other_than_o_on_the_launch_screen_opens_no_folder_picker_and_keeps_the_launch_text(qtbot):
    viewer = shown_launch_viewer(qtbot)
    launch_text = shown_texts(viewer)

    modal = modal_opened_by_key(qtbot, viewer, Qt.Key.Key_X)

    assert modal is None
    assert shown_texts(viewer) == launch_text


def test_choosing_a_folder_in_the_o_picker_starts_that_folders_slideshow_at_its_first_item(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = Viewer(player_options=SILENT, folder_picker=lambda: tmp_path)
    qtbot.addWidget(viewer)
    viewer.show()
    qtbot.waitExposed(viewer)

    qtbot.keyClick(viewer, Qt.Key.Key_O)

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("red")
