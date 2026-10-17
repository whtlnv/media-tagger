import subprocess
import time

import pytest
from PySide6.QtCore import Qt

from mediatagger.test_video import make_clip, wait_until_playing
from mediatagger.test_viewer import make_image, make_surface_ready, shown_viewer_on, wait_until_loaded
from mediatagger.test_viewer_video import frame_stepping_viewer_on, viewer_paused_at_10_seconds
from mediatagger.test_viewer_zoom import viewer_playing_a_clip_in
from mediatagger.viewer import Viewer


def make_silent_long_gop_clip(path):
    """20 s at 25 fps with no sound and keyframes only at 0:00 and 0:10, like a camera's: mpv reverses such a file only
    from its demuxer cache."""
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=duration=20:size=64x48:rate=25", "-c:v", "libx264",
         "-g", "250", "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )
    return path


def test_pressing_b_in_the_viewer_on_a_playing_video_makes_it_play_backwards_its_position_going_down(qtbot, tmp_path):
    viewer, engine = viewer_playing_a_clip_in(qtbot, tmp_path)
    viewer.video_player.seek_to(15)

    qtbot.keyClick(viewer, Qt.Key.Key_B)

    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos < 14, timeout=5)


def test_pressing_b_again_in_the_viewer_on_a_video_playing_backwards_plays_it_forwards_its_position_going_up(qtbot, tmp_path):
    viewer, engine = viewer_playing_a_clip_in(qtbot, tmp_path)
    viewer.video_player.seek_to(15)
    qtbot.keyClick(viewer, Qt.Key.Key_B)
    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos < 14, timeout=5)

    qtbot.keyClick(viewer, Qt.Key.Key_B)

    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 15, timeout=5)


def test_pressing_b_in_the_viewer_on_an_image_keeps_showing_it_and_leaves_the_idle_player_set_to_play_forwards(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_B)

    assert viewer.slideshow.current == tmp_path / "IMG_1.png"
    assert viewer.video_player.engine.play_direction == "forward"


def test_a_video_shown_after_one_playing_backwards_starts_from_its_beginning_playing_forwards(qtbot, tmp_path):
    second = make_clip(tmp_path / "IMG_2.mp4", duration=30)
    viewer, engine = viewer_playing_a_clip_in(qtbot, tmp_path)
    qtbot.keyClick(viewer, Qt.Key.Key_B)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)
    make_surface_ready(viewer)
    wait_until_loaded(engine, second)
    wait_until_playing(engine)

    assert engine.play_direction == "forward"
    assert engine.time_pos < 5


def test_pressing_0_in_the_viewer_on_a_video_playing_backwards_plays_it_forwards_its_position_going_up(qtbot, tmp_path):
    viewer, engine = viewer_playing_a_clip_in(qtbot, tmp_path)
    viewer.video_player.seek_to(15)
    qtbot.keyClick(viewer, Qt.Key.Key_B)
    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos < 14, timeout=5)

    qtbot.keyClick(viewer, Qt.Key.Key_0)

    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 15, timeout=5)


def test_a_video_playing_backwards_that_reaches_its_start_goes_on_playing_backwards_from_near_its_end(qtbot, tmp_path):
    viewer, engine = viewer_playing_a_clip_in(qtbot, tmp_path)
    viewer.video_player.seek_to(1)
    qtbot.keyClick(viewer, Qt.Key.Key_B)

    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 25, timeout=5)
    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos < 29, timeout=5)


def test_pressing_up_on_a_video_playing_backwards_seeks_10_s_later_and_it_goes_on_playing_backwards(qtbot, tmp_path):
    viewer, engine = viewer_playing_a_clip_in(qtbot, tmp_path)
    viewer.video_player.seek_to(10)
    qtbot.keyClick(viewer, Qt.Key.Key_B)

    qtbot.keyClick(viewer, Qt.Key.Key_Up)

    assert engine.time_pos == pytest.approx(20, abs=1)
    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos < 18.5, timeout=5)


def test_pressing_u_on_a_paused_video_turned_backwards_shows_its_next_frame_later_in_the_video(qtbot, tmp_path):
    viewer = viewer_paused_at_10_seconds(qtbot, tmp_path)
    engine = viewer.video_player.engine
    with engine.prepare_and_wait_for_event("playback_restart", timeout=5):  # a step pressed before the turn lands is lost
        qtbot.keyClick(viewer, Qt.Key.Key_B)

    qtbot.keyClick(viewer, Qt.Key.Key_U)

    engine.wait_for_property("time-pos", lambda time_pos: time_pos == pytest.approx(10.1, abs=0.01), timeout=5)
    assert engine.pause is True


def test_pressing_e_on_a_paused_video_turned_backwards_shows_its_previous_frame_earlier_in_the_video(qtbot, tmp_path):
    viewer = viewer_paused_at_10_seconds(qtbot, tmp_path)
    engine = viewer.video_player.engine
    with engine.prepare_and_wait_for_event("playback_restart", timeout=5):  # a step pressed before the turn lands is lost
        qtbot.keyClick(viewer, Qt.Key.Key_B)

    qtbot.keyClick(viewer, Qt.Key.Key_E)

    engine.wait_for_property("time-pos", lambda time_pos: time_pos == pytest.approx(9.9, abs=0.01), timeout=5)
    assert engine.pause is True


def test_pressing_b_on_a_silent_clip_mid_way_between_its_keyframes_returns_at_once_and_plays_it_backwards(qtbot, tmp_path):
    make_silent_long_gop_clip(tmp_path / "IMG_1.mp4")
    viewer = frame_stepping_viewer_on(qtbot, tmp_path)
    engine = viewer.video_player.engine
    wait_until_playing(engine)
    viewer.video_player.seek_to(9)

    pressed = time.monotonic()
    qtbot.keyClick(viewer, Qt.Key.Key_B)

    assert time.monotonic() - pressed < 0.3  # mpv's restart can wait on a frame drawn by the very thread b blocks
    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos < 8.5, timeout=5)


def test_the_viewers_player_demuxes_on_its_own_playback_thread(qtbot):
    viewer = Viewer(player_options={"ao": "null"})
    qtbot.addWidget(viewer)

    # mpv 0.41's demuxer thread can miss the request for the packets before a keyframe when a silent clip starts playing
    # backwards through the render API, and the clip then never moves (seen under load on the Mac)
    assert viewer.video_player.engine["demuxer-thread"] is False
