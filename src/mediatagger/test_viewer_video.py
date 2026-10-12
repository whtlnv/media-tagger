import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from mediatagger.mpv_surface import MpvSurface
from mediatagger.test_video import make_clip, wait_until_playing
from mediatagger.test_viewer import (
    centre_colour, make_image, make_surface_ready, run_python_offscreen, shown_texts, shown_viewer_on, shows_unsupported_placeholder,
    shows_video_surface, SILENT, unready_viewer_on, wait_until_loaded,
)
from mediatagger.viewer import UNSUPPORTED_TEXT, Viewer


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
    # mpv seeks asynchronously, so wait for the new position rather than reading it at once
    engine.wait_for_property("time-pos", lambda time_pos: time_pos == pytest.approx(before + 10, abs=1), timeout=5)


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

    qtbot.waitUntil(lambda: shown_texts(viewer) == [UNSUPPORTED_TEXT], timeout=5000)
    assert not shows_video_surface(viewer)


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

    engine.wait_for_property("time-pos", lambda time_pos: time_pos == pytest.approx(10, abs=1), timeout=5)


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


def test_a_digit_key_in_the_viewer_on_an_image_keeps_showing_the_image_and_loads_no_video(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_clip(tmp_path / "IMG_2.mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_5)

    assert centre_colour(viewer) == QColor("red")
    assert not shows_video_surface(viewer)
    assert viewer.video_player.engine.path is None


def test_a_viewer_made_without_extra_player_options_turns_off_mpvs_direct_rendering_decoder_buffers(qtbot):
    viewer = Viewer()
    qtbot.addWidget(viewer)

    assert viewer.video_player.engine["vd-lavc-dr"] is False


def test_a_viewer_made_with_extra_player_options_keeps_them_and_still_turns_off_direct_rendering(qtbot):
    viewer = Viewer(player_options={"ao": "null"})
    qtbot.addWidget(viewer)

    assert [output["name"] for output in viewer.video_player.engine["ao"]] == ["null"]
    assert viewer.video_player.engine["vd-lavc-dr"] is False
