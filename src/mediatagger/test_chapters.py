import pytest
from PySide6.QtCore import Qt

from mediatagger.grid import MOMENTS_BADGE
from mediatagger.library import Library
from mediatagger.status_bar import TAGS_CANT_BE_SAVED_HERE_TEXT
from mediatagger.test_grid import painted_texts
from mediatagger.test_video import wait_until_playing
from mediatagger.test_video_controls import is_tick_coloured
from mediatagger.test_viewer import make_surface_ready, shown_texts
from mediatagger.test_viewer_library import (
    drive_with_a_tag_library_holding_one_clip, drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, made_read_only, make_tag_library_drive, shown_viewer_on_drive, status_bar_texts,
    visible_tag_prompt_texts,
)
from mediatagger.test_window_cheat_sheet import window_on_the_drive


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


def test_the_video_keeps_playing_while_the_prompt_opened_by_c_is_open(qtbot, tmp_path):
    viewer, _drive, _folder = viewer_playing_a_clip_on_a_drive_with_a_library(qtbot, tmp_path)
    engine = viewer.video_player.engine
    qtbot.keyClick(viewer, Qt.Key.Key_C)
    opened_at = engine.time_pos

    qtbot.keyClicks(viewer.tag_prompt.input, "goal")

    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > opened_at + 0.5, timeout=5)
    assert engine.pause is False


def test_esc_in_the_prompt_opened_by_c_closes_it_and_records_no_tag_and_no_moment(qtbot, tmp_path):
    viewer, drive, folder = viewer_playing_a_clip_on_a_drive_with_a_library(qtbot, tmp_path)
    qtbot.keyClick(viewer, Qt.Key.Key_C)
    qtbot.keyClicks(viewer.tag_prompt.input, "goal")

    qtbot.keyClick(viewer.tag_prompt.input, Qt.Key.Key_Escape)

    library = Library.open(drive)
    assert visible_tag_prompt_texts(viewer) == []
    assert (library.tags(folder / "IMG_1.mp4"), library.moments(folder / "IMG_1.mp4")) == ([], [])


def test_entering_minus_goal_in_the_prompt_opened_by_c_on_a_video_tagged_goal_leaves_goal_and_its_moments_and_adds_no_tag(qtbot, tmp_path):
    viewer, drive, folder = viewer_playing_a_clip_on_a_drive_with_a_library(qtbot, tmp_path)
    clip = folder / "IMG_1.mp4"
    Library.open(drive).add_chapter(clip, "goal", 1)
    qtbot.keyClick(viewer, Qt.Key.Key_C)

    qtbot.keyClicks(viewer.tag_prompt.input, "-goal")
    qtbot.keyClick(viewer.tag_prompt.input, Qt.Key.Key_Return)

    library = Library.open(drive)
    assert library.tags(clip) == ["goal"]
    assert [moment.seconds for moment in library.moments(clip)] == [1]


def test_after_entering_a_chapter_with_c_the_tag_overlay_lists_its_tag(qtbot, tmp_path):
    viewer, _drive, _folder = viewer_playing_a_clip_on_a_drive_with_a_library(qtbot, tmp_path)
    qtbot.keyClick(viewer, Qt.Key.Key_C)

    qtbot.keyClicks(viewer.tag_prompt.input, "goal")
    qtbot.keyClick(viewer.tag_prompt.input, Qt.Key.Key_Return)

    assert "goal" in shown_texts(viewer)


def ticks_on_the_progress_bar(viewer):
    """The x of each tick along the bottom row of the viewer's progress bar."""
    image = viewer.progress_bar.grab().toImage()
    row = image.height() - 2
    xs = [x for x in range(image.width()) if is_tick_coloured(image.pixelColor(x, row))]
    return [x for x in xs if x - 1 not in xs]


def test_after_a_chapter_is_added_with_c_its_tick_shows_on_the_progress_bar_at_once(qtbot, tmp_path):
    viewer, _drive, _folder = viewer_playing_a_clip_on_a_drive_with_a_library(qtbot, tmp_path)
    qtbot.keyClick(viewer, Qt.Key.Key_C)
    qtbot.keyClicks(viewer.tag_prompt.input, "goal")

    qtbot.keyClick(viewer.tag_prompt.input, Qt.Key.Key_Return)

    assert len(ticks_on_the_progress_bar(viewer)) == 1


def test_after_minus_goal_is_entered_with_t_the_ticks_of_moments_that_carried_only_goal_leave_the_progress_bar_at_once(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=30)
    Library.open(drive).add_chapter(folder / "IMG_1.mp4", "goal", 5)
    Library.open(drive).add_chapter(folder / "IMG_1.mp4", "save", 20)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    wait_until_playing(viewer.video_player.engine)
    qtbot.waitUntil(lambda: len(ticks_on_the_progress_bar(viewer)) == 2, timeout=5000)

    enter_in_tag_prompt(qtbot, viewer, "-goal")

    assert len(ticks_on_the_progress_bar(viewer)) == 1


def viewer_paused_at(qtbot, tmp_path, seconds, moments, duration=65, tag="goal"):
    """The viewer paused seconds into the drive's clip, which has a chapter of the tag at each of moments."""
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=duration)
    for moment in moments:
        Library.open(drive).add_chapter(folder / "IMG_1.mp4", tag, moment)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    wait_until_playing(engine)
    engine.pause = True
    with engine.prepare_and_wait_for_event("playback_restart", timeout=5):
        engine.seek(seconds, reference="absolute", precision="exact")
    return viewer


def test_pressing_period_on_a_video_at_0_20_with_moments_at_0_10_and_0_30_seeks_to_0_30(qtbot, tmp_path):
    viewer = viewer_paused_at(qtbot, tmp_path, 20, moments=[10, 30])

    qtbot.keyClick(viewer, Qt.Key.Key_Period)

    assert viewer.video_player.engine.time_pos == pytest.approx(30, abs=0.2)


def test_pressing_period_on_a_video_past_its_last_moment_leaves_the_playback_position_unchanged(qtbot, tmp_path):
    viewer = viewer_paused_at(qtbot, tmp_path, 40, moments=[10, 30])

    qtbot.keyClick(viewer, Qt.Key.Key_Period)

    assert viewer.video_player.engine.time_pos == pytest.approx(40, abs=0.3)


def test_pressing_comma_on_a_video_at_0_20_with_moments_at_0_10_and_0_30_seeks_to_0_10(qtbot, tmp_path):
    viewer = viewer_paused_at(qtbot, tmp_path, 20, moments=[10, 30])

    qtbot.keyClick(viewer, Qt.Key.Key_Comma)

    assert viewer.video_player.engine.time_pos == pytest.approx(10, abs=0.2)


def test_pressing_comma_right_after_period_landed_on_a_moment_seeks_to_the_moment_before_it(qtbot, tmp_path):
    viewer = viewer_paused_at(qtbot, tmp_path, 20, moments=[10, 30])
    qtbot.keyClick(viewer, Qt.Key.Key_Period)

    qtbot.keyClick(viewer, Qt.Key.Key_Comma)

    assert viewer.video_player.engine.time_pos == pytest.approx(10, abs=0.2)


def test_pressing_comma_on_a_video_before_its_first_moment_leaves_the_playback_position_unchanged(qtbot, tmp_path):
    viewer = viewer_paused_at(qtbot, tmp_path, 5, moments=[10, 30])

    qtbot.keyClick(viewer, Qt.Key.Key_Comma)

    assert viewer.video_player.engine.time_pos == pytest.approx(5, abs=0.3)


@pytest.mark.parametrize("key", [Qt.Key.Key_Period, Qt.Key.Key_Comma])
def test_pressing_period_or_comma_on_a_video_with_no_moments_leaves_the_playback_position_unchanged(qtbot, tmp_path, key):
    viewer = viewer_paused_at(qtbot, tmp_path, 20, moments=[])

    qtbot.keyClick(viewer, key)

    assert viewer.video_player.engine.time_pos == pytest.approx(20, abs=0.3)


@pytest.mark.parametrize(("start", "key", "shown"), [(20, Qt.Key.Key_Period, "save · 0:30 / 1:05"), (40, Qt.Key.Key_Comma, "save · 0:30 / 1:05")])
def test_a_jump_shows_the_progress_bar_reading_the_moments_tag_before_the_time(qtbot, tmp_path, start, key, shown):
    viewer = viewer_paused_at(qtbot, tmp_path, start, moments=[30], tag="save")

    qtbot.keyClick(viewer, key)

    assert viewer.progress_bar.isVisible()
    assert viewer.progress_bar.text() == shown


def test_after_a_jump_a_key_other_than_period_or_comma_shows_the_progress_bar_without_a_tag_name(qtbot, tmp_path):
    viewer = viewer_paused_at(qtbot, tmp_path, 20, moments=[30], tag="save")
    qtbot.keyClick(viewer, Qt.Key.Key_Period)

    qtbot.keyClick(viewer, Qt.Key.Key_V)

    assert viewer.progress_bar.text() == "0:30 / 1:05"


def test_after_adding_a_chapter_with_c_esc_back_to_the_grid_shows_the_videos_tile_with_its_moments_badge(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=30)
    Library.open(drive).add_chapter(folder / "IMG_1.mp4", "kickoff", 0)
    window = window_on_the_drive(qtbot, drive, folder)
    viewer = window.viewer
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 2, timeout=5)
    qtbot.keyClick(viewer, Qt.Key.Key_C)
    qtbot.keyClicks(viewer.tag_prompt.input, "goal")
    qtbot.keyClick(viewer.tag_prompt.input, Qt.Key.Key_Return)

    qtbot.keyClick(viewer, Qt.Key.Key_Escape)

    grid = window.stack.currentWidget()
    assert f"{MOMENTS_BADGE} 2" in painted_texts(grid, 0)


def test_a_chapter_added_with_c_on_a_video_that_cannot_play_is_recorded_at_its_start(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    (drive / "Clips").mkdir()
    clip = drive / "Clips" / "IMG_1.mp4"
    clip.write_bytes(b"not really an mp4")
    viewer = shown_viewer_on_drive(qtbot, drive / "Clips", drive, lambda question: False)
    make_surface_ready(viewer)

    enter_in_tag_prompt(qtbot, viewer, "goal", key=Qt.Key.Key_C)

    assert [moment.seconds for moment in Library.open(drive).moments(clip)] == [0]
