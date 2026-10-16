import pytest
from PySide6.QtCore import Qt

from mediatagger.chapter_list import ChapterList
from mediatagger.grid import MOMENTS_BADGE
from mediatagger.library import Library
from mediatagger.status_bar import TAGS_CANT_BE_SAVED_HERE_TEXT
from mediatagger.test_grid import painted_texts
from mediatagger.test_video import make_clip, wait_until_playing
from mediatagger.test_video_controls import is_tick_coloured
from mediatagger.test_viewer import make_surface_ready, shown_texts
from mediatagger.test_viewer_library import (
    drive_with_a_tag_library_holding_one_clip, drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, made_read_only, shown_viewer_on_drive, status_bar_texts,
    visible_tag_prompt_texts,
)
from mediatagger.test_window_cheat_sheet import sheet_is_shown, window_on_the_drive


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


def viewer_playing_a_clip_with_chapters(qtbot, tmp_path, chapters, duration=65):
    """The viewer playing the drive's clip, which has each of the chapters, (text, seconds), added beforehand."""
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=duration)
    for text, seconds in chapters:
        Library.open(drive).add_chapter(folder / "IMG_1.mp4", text, seconds)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    wait_until_playing(viewer.video_player.engine)
    return viewer


def shown_chapter_lines(viewer):
    """The lines of the chapter list, if it is shown; None if it isn't."""
    chapter_list = viewer.findChild(ChapterList)
    if chapter_list is None or not chapter_list.isVisible():
        return None
    return [chapter_list.item(row).text() for row in range(chapter_list.count())]


def test_pressing_l_on_a_video_with_moments_lists_them_in_time_order_one_line_per_moment_with_its_tags(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, [("save", 40), ("goal people:ana", 10)])

    qtbot.keyClick(viewer, Qt.Key.Key_L)

    assert shown_chapter_lines(viewer) == ["0:10 goal, people:ana", "0:40 save"]


def test_pressing_l_on_a_video_with_no_moments_shows_a_list_reading_no_chapters(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, [])

    qtbot.keyClick(viewer, Qt.Key.Key_L)

    assert shown_chapter_lines(viewer) == ["No chapters"]


def test_a_moment_from_an_hour_on_is_listed_as_h_mm_ss(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, [("goal", 3723)])

    qtbot.keyClick(viewer, Qt.Key.Key_L)

    assert shown_chapter_lines(viewer) == ["1:02:03 goal"]


def test_pressing_l_while_the_chapter_list_is_shown_hides_it(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, [("goal", 10)])
    qtbot.keyClick(viewer, Qt.Key.Key_L)

    qtbot.keyClick(viewer, Qt.Key.Key_L)

    assert shown_chapter_lines(viewer) is None


def test_pressing_l_on_a_shown_image_shows_no_chapter_list(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_L)

    assert shown_chapter_lines(viewer) is None


def highlighted_chapter_line(viewer):
    chapter_list = viewer.findChild(ChapterList)
    item = chapter_list.currentItem()
    return item.text() if item is not None and item.isSelected() else None


THREE_CHAPTERS = [("kickoff", 5), ("goal", 20), ("save", 40)]


def test_when_the_chapter_list_opens_its_first_line_is_highlighted(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, THREE_CHAPTERS)

    qtbot.keyClick(viewer, Qt.Key.Key_L)

    assert highlighted_chapter_line(viewer) == "0:05 kickoff"


def test_down_in_the_chapter_list_highlights_the_next_line(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, THREE_CHAPTERS)
    qtbot.keyClick(viewer, Qt.Key.Key_L)

    qtbot.keyClick(viewer, Qt.Key.Key_Down)

    assert highlighted_chapter_line(viewer) == "0:20 goal"


def test_up_in_the_chapter_list_highlights_the_previous_line(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, THREE_CHAPTERS)
    qtbot.keyClick(viewer, Qt.Key.Key_L)
    qtbot.keyClick(viewer, Qt.Key.Key_Down)
    qtbot.keyClick(viewer, Qt.Key.Key_Down)

    qtbot.keyClick(viewer, Qt.Key.Key_Up)

    assert highlighted_chapter_line(viewer) == "0:20 goal"


@pytest.mark.parametrize("key", [Qt.Key.Key_Up, Qt.Key.Key_Down])
def test_up_or_down_while_the_chapter_list_is_shown_leaves_the_playback_position_unchanged(qtbot, tmp_path, key):
    viewer = viewer_paused_at(qtbot, tmp_path, 30, moments=[5, 20, 40])
    qtbot.keyClick(viewer, Qt.Key.Key_L)

    qtbot.keyClick(viewer, key)

    assert viewer.video_player.engine.time_pos == pytest.approx(30, abs=0.3)


def test_the_video_keeps_playing_while_the_chapter_list_is_shown(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, THREE_CHAPTERS)
    engine = viewer.video_player.engine
    qtbot.keyClick(viewer, Qt.Key.Key_L)
    shown_at = engine.time_pos

    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > shown_at + 0.5, timeout=5)

    assert shown_chapter_lines(viewer) is not None
    assert engine.pause is False


def test_enter_in_the_chapter_list_seeks_to_the_highlighted_moment_and_hides_the_list(qtbot, tmp_path):
    viewer = viewer_paused_at(qtbot, tmp_path, 30, moments=[5, 20, 40])
    qtbot.keyClick(viewer, Qt.Key.Key_L)
    qtbot.keyClick(viewer, Qt.Key.Key_Down)

    qtbot.keyClick(viewer, Qt.Key.Key_Return)

    assert viewer.video_player.engine.time_pos == pytest.approx(20, abs=0.2)
    assert shown_chapter_lines(viewer) is None


def test_enter_in_the_chapter_list_does_not_pause_the_video(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, THREE_CHAPTERS)
    qtbot.keyClick(viewer, Qt.Key.Key_L)

    qtbot.keyClick(viewer, Qt.Key.Key_Return)

    assert viewer.video_player.engine.pause is False


def test_esc_in_the_chapter_list_hides_it_and_leaves_the_viewer_showing_the_video(qtbot, tmp_path):
    left = []
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, THREE_CHAPTERS)
    viewer.on_escape = lambda: left.append(True)
    qtbot.keyClick(viewer, Qt.Key.Key_L)

    qtbot.keyClick(viewer, Qt.Key.Key_Escape)

    assert shown_chapter_lines(viewer) is None
    assert left == []


def test_backspace_in_the_chapter_list_deletes_the_highlighted_moment_its_line_and_tick_go_and_its_tags_stay(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, THREE_CHAPTERS)
    qtbot.waitUntil(lambda: len(ticks_on_the_progress_bar(viewer)) == 3, timeout=5000)
    qtbot.keyClick(viewer, Qt.Key.Key_L)
    qtbot.keyClick(viewer, Qt.Key.Key_Down)

    qtbot.keyClick(viewer, Qt.Key.Key_Backspace)

    assert shown_chapter_lines(viewer) == ["0:05 kickoff", "0:40 save"]
    assert len(ticks_on_the_progress_bar(viewer)) == 2
    assert Library.open(viewer.session.library.root).tags(viewer.slideshow.current) == ["goal", "kickoff", "save"]


def test_backspace_in_the_chapter_list_on_a_read_only_drive_keeps_the_moment_and_says_tags_cant_be_saved_here(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=30)
    Library.open(drive).add_chapter(folder / "IMG_1.mp4", "goal", 5)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
        make_surface_ready(viewer)
        wait_until_playing(viewer.video_player.engine)
        qtbot.keyClick(viewer, Qt.Key.Key_L)

        qtbot.keyClick(viewer, Qt.Key.Key_Backspace)

        moments = Library.open(drive).moments(folder / "IMG_1.mp4")
    assert shown_chapter_lines(viewer) == ["0:05 goal"]
    assert [moment.seconds for moment in moments] == [5]
    assert TAGS_CANT_BE_SAVED_HERE_TEXT in status_bar_texts(viewer)


def test_backspace_in_the_chapter_list_when_the_drive_fails_keeps_the_moment_listed_and_says_tags_cant_be_saved_here(qtbot, tmp_path, monkeypatch):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, THREE_CHAPTERS)
    qtbot.keyClick(viewer, Qt.Key.Key_L)
    monkeypatch.setattr(Library, "delete_moment", lambda self, video, seconds: (_ for _ in ()).throw(OSError(5, "Input/output error")))

    qtbot.keyClick(viewer, Qt.Key.Key_Backspace)

    assert shown_chapter_lines(viewer) == ["0:05 kickoff", "0:20 goal", "0:40 save"]
    assert TAGS_CANT_BE_SAVED_HERE_TEXT in status_bar_texts(viewer)


@pytest.mark.parametrize("key", [Qt.Key.Key_Space, Qt.Key.Key_Right])
def test_moving_to_another_item_while_the_chapter_list_is_shown_hides_it(qtbot, tmp_path, key):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=30)
    make_clip(folder / "IMG_2.mp4", duration=30)
    Library.open(drive).add_chapter(folder / "IMG_1.mp4", "goal", 5)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    wait_until_playing(viewer.video_player.engine)
    qtbot.keyClick(viewer, Qt.Key.Key_L)

    qtbot.keyClick(viewer, key)

    assert viewer.slideshow.current.name == "IMG_2.mp4"
    assert shown_chapter_lines(viewer) is None


def test_with_the_cheat_sheet_and_the_chapter_list_shown_esc_hides_only_the_sheet_and_a_second_esc_the_list(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=30)
    Library.open(drive).add_chapter(folder / "IMG_1.mp4", "goal", 5)
    window = window_on_the_drive(qtbot, drive, folder)
    viewer = window.viewer
    make_surface_ready(viewer)
    wait_until_playing(viewer.video_player.engine)
    qtbot.keyClick(viewer, Qt.Key.Key_L)
    qtbot.keyClick(viewer, Qt.Key.Key_H)

    qtbot.keyClick(viewer, Qt.Key.Key_Escape)
    after_the_first = (sheet_is_shown(window), shown_chapter_lines(viewer))
    qtbot.keyClick(viewer, Qt.Key.Key_Escape)

    assert after_the_first == (False, ["0:05 goal"])
    assert shown_chapter_lines(viewer) is None
    assert window.stack.currentWidget() is viewer


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


def test_keys_the_tag_prompt_passes_on_never_reach_the_chapter_list_open_behind_it(qtbot, tmp_path):
    viewer = viewer_playing_a_clip_with_chapters(qtbot, tmp_path, THREE_CHAPTERS)
    qtbot.keyClick(viewer, Qt.Key.Key_L)
    qtbot.keyClick(viewer, Qt.Key.Key_C)

    qtbot.keyClick(viewer.tag_prompt.input, Qt.Key.Key_Down)
    qtbot.keyClick(viewer.tag_prompt.input, Qt.Key.Key_Backspace)

    assert highlighted_chapter_line(viewer) == "0:05 kickoff"
    assert len(shown_chapter_lines(viewer)) == 3
