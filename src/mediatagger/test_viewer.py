import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from mediatagger.test_video import make_clip

from mediatagger.viewer import Viewer


def make_image(path, color):
    image = QImage(64, 48, QImage.Format.Format_RGB32)
    image.fill(QColor(color))
    image.save(str(path))
    return path


def shown_viewer_on(qtbot, folder):
    viewer = Viewer(folder)
    qtbot.addWidget(viewer)
    viewer.resize(400, 300)
    viewer.show()
    qtbot.waitExposed(viewer)
    return viewer


def centre_colour_of_viewer_on(qtbot, folder):
    viewer = shown_viewer_on(qtbot, folder)
    frame = viewer.grab().toImage()
    return frame.pixelColor(frame.width() // 2, frame.height() // 2)


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
    viewer.video_player.engine.wait_for_property("path", lambda path: path == str(clip), timeout=5)


def test_a_viewer_opened_on_a_folder_whose_first_item_is_an_image_shows_no_video_surface_and_loads_no_clip(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_clip(tmp_path / "IMG_2.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)

    surface = viewer.findChild(QOpenGLWidget)
    assert surface is None or not surface.isVisible()
    assert viewer.video_player.engine.path is None


def test_pressing_space_in_the_viewer_on_a_video_followed_by_a_red_image_hides_the_video_surface_and_paints_red(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    surface = viewer.findChild(QOpenGLWidget)
    assert surface is None or not surface.isVisible()
    frame = viewer.grab().toImage()
    assert frame.pixelColor(frame.width() // 2, frame.height() // 2) == QColor("red")


def test_pressing_space_in_the_viewer_on_a_video_followed_by_an_image_leaves_the_player_stopped(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.video_player.engine.wait_for_property("path", lambda path: path == str(clip), timeout=5)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    assert viewer.video_player.engine.path is None


def test_the_viewers_video_player_renders_through_libmpv_into_the_surface_and_plays_sound_on_the_default_audio_output(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)

    engine = viewer.video_player.engine
    assert [output["name"] for output in engine.vo] == ["libmpv"]
    assert "null" not in [output["name"] for output in engine.ao]


def test_pressing_m_in_the_viewer_on_a_video_mutes_the_video_player(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.video_player.engine.wait_for_property("path", lambda path: path == str(clip), timeout=5)

    qtbot.keyClick(viewer, Qt.Key.Key_M)

    assert viewer.video_player.engine.mute is True


def test_pressing_right_in_the_viewer_on_a_red_image_followed_by_a_blue_image_paints_blue_and_left_paints_red_again(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_Right)
    frame = viewer.grab().toImage()
    assert frame.pixelColor(frame.width() // 2, frame.height() // 2) == QColor("blue")

    qtbot.keyClick(viewer, Qt.Key.Key_Left)
    frame = viewer.grab().toImage()
    assert frame.pixelColor(frame.width() // 2, frame.height() // 2) == QColor("red")


def test_pressing_space_in_the_viewer_on_an_image_followed_by_a_video_shows_the_video_surface_and_plays_that_clip(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    clip = make_clip(tmp_path / "IMG_2.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    surface = viewer.findChild(QOpenGLWidget)
    assert surface is not None and surface.isVisible()
    viewer.video_player.engine.wait_for_property("path", lambda path: path == str(clip), timeout=5)


def test_pressing_p_in_the_viewer_on_a_video_pauses_it_and_up_seeks_it_forward(qtbot, tmp_path):
    make_clip(tmp_path / "IMG_1.mp4", duration=30)
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)
    engine = viewer.video_player.engine
    engine.wait_for_property("time-pos", lambda time_pos: time_pos is not None, timeout=5)

    qtbot.keyClick(viewer, Qt.Key.Key_P)
    assert engine.pause is True

    before = engine.time_pos
    qtbot.keyClick(viewer, Qt.Key.Key_Up)
    assert engine.time_pos == pytest.approx(before + 10, abs=1)


def test_a_viewer_draws_a_wide_red_image_fitted_to_a_square_window_with_black_above_and_below_it(qtbot, tmp_path):
    image = QImage(200, 100, QImage.Format.Format_RGB32)
    image.fill(QColor("red"))
    image.save(str(tmp_path / "IMG_1.png"))
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.resize(300, 300)
    qtbot.waitUntil(lambda: viewer.size().width() == viewer.size().height())

    frame = viewer.grab().toImage()
    middle = frame.width() // 2
    assert frame.pixelColor(middle, frame.height() // 2) == QColor("red")
    assert frame.pixelColor(middle, 10) == QColor("black")
    assert frame.pixelColor(middle, frame.height() - 10) == QColor("black")
