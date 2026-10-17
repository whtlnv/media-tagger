from PySide6.QtCore import Qt

from mediatagger.test_video import make_clip, wait_until_playing
from mediatagger.test_viewer import make_image, make_surface_ready, shown_viewer_on, wait_until_loaded
from mediatagger.test_viewer_zoom import viewer_playing_a_clip_in


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
