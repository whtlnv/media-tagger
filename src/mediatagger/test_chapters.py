from PySide6.QtCore import Qt

from mediatagger.test_video import wait_until_playing
from mediatagger.test_viewer import make_surface_ready
from mediatagger.library import Library
from mediatagger.status_bar import TAGS_CANT_BE_SAVED_HERE_TEXT
from mediatagger.test_viewer_library import (
    drive_with_a_tag_library_holding_one_clip, drive_with_a_tag_library_holding_one_image, made_read_only, shown_viewer_on_drive, status_bar_texts,
    visible_tag_prompt_texts,
)


def viewer_playing_a_clip_on_a_drive_with_a_library(qtbot, tmp_path, duration=30):
    """The viewer showing the drive's one clip, IMG_1.mp4, playing; the drive and its folder come back too."""
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=duration)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    wait_until_playing(viewer.video_player.engine)
    return viewer, drive, folder


def test_pressing_c_on_a_shown_video_opens_the_tag_prompt(qtbot, tmp_path):
    viewer, _drive, _folder = viewer_playing_a_clip_on_a_drive_with_a_library(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_C)

    assert visible_tag_prompt_texts(viewer) == [""]


def test_pressing_c_on_a_shown_image_opens_no_tag_prompt(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_C)

    assert visible_tag_prompt_texts(viewer) == []


def test_pressing_c_on_a_video_on_a_read_only_drive_opens_no_prompt_and_says_tags_cant_be_saved_here(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=30)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
        make_surface_ready(viewer)
        wait_until_playing(viewer.video_player.engine)

        qtbot.keyClick(viewer, Qt.Key.Key_C)

    assert visible_tag_prompt_texts(viewer) == []
    assert TAGS_CANT_BE_SAVED_HERE_TEXT in status_bar_texts(viewer)


def test_entering_goal_in_the_prompt_opened_by_c_records_a_moment_at_the_time_c_was_pressed_not_when_enter_was(qtbot, tmp_path):
    viewer, drive, folder = viewer_playing_a_clip_on_a_drive_with_a_library(qtbot, tmp_path)
    engine = viewer.video_player.engine
    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 1, timeout=5)
    pressed_at = engine.time_pos
    qtbot.keyClick(viewer, Qt.Key.Key_C)
    qtbot.wait(1500)

    qtbot.keyClicks(viewer.tag_prompt.input, "goal")
    qtbot.keyClick(viewer.tag_prompt.input, Qt.Key.Key_Return)

    [moment] = Library.open(drive).moments(folder / "IMG_1.mp4")
    assert moment.tags == ["goal"]
    assert abs(moment.seconds - pressed_at) < 0.3
