from PySide6.QtCore import Qt

from mediatagger.test_viewer_zoom import viewer_playing_a_clip_in


def test_pressing_b_in_the_viewer_on_a_playing_video_makes_it_play_backwards_its_position_going_down(qtbot, tmp_path):
    viewer, engine = viewer_playing_a_clip_in(qtbot, tmp_path)
    viewer.video_player.seek_to(15)

    qtbot.keyClick(viewer, Qt.Key.Key_B)

    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos < 14, timeout=5)
