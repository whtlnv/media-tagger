import errno
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QLabel, QStackedWidget

from mediatagger.backup import back_up
from mediatagger.drive_session import BACKUP_FAILED_TEXT, CREATE_LIBRARY_QUESTION, RESTORE_LIBRARY_QUESTION
from mediatagger.grid import TAG_BADGE, TILE_ROLE, Grid
from mediatagger.library import Library
from mediatagger.status_bar import READ_ONLY_STATUS_TEXT, TAGS_CANT_BE_SAVED_HERE_TEXT, StatusBar
from mediatagger.test_grid import painted_texts
from mediatagger.test_tag_prompt import listed
from mediatagger.test_video import make_clip
from mediatagger.test_viewer_backup import tags_in_newest_backup
from mediatagger.test_viewer import SILENT, make_image, make_surface_ready, show_exposed, shown_texts, wait_until_loaded
from mediatagger.test_viewer_library import (
    decline_noting_the_question_in, drive_with_a_tag_library_holding_one_image, drive_without_a_tag_library_holding_one_image, enter_in_tag_prompt,
    frame_in, made_read_only, overwrite_tags_db_with_garbage, resize_and_wait, visible_tag_prompt_texts, visible_tag_prompts,
)
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders
from mediatagger.viewer import Viewer
from mediatagger.window import Window


def test_the_window_opened_on_a_folder_path_shows_the_slideshow_of_that_folder_at_its_first_item(qtbot, tmp_path):
    make_image(tmp_path / "b.jpg", "blue")
    make_image(tmp_path / "a.jpg", "red")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)

    shown = window.findChild(QStackedWidget).currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == tmp_path / "a.jpg"


def test_the_window_opened_on_a_relative_path_to_a_file_shows_that_file_in_the_viewer_as_the_absolute_path_does(qtbot, tmp_path, monkeypatch):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    monkeypatch.chdir(tmp_path)
    window = Window(Path("b.jpg"), player_options=SILENT)
    qtbot.addWidget(window)

    shown = window.findChild(QStackedWidget).currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == tmp_path / "b.jpg"


def test_in_the_windows_viewer_esc_shows_the_grid_of_the_current_items_folder_with_the_cursor_on_that_item(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(Qt.ItemDataRole.DisplayRole) == "a.jpg"


def test_in_the_windows_viewer_esc_after_stepping_to_the_second_item_puts_the_grid_cursor_on_the_second_item(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(Qt.ItemDataRole.DisplayRole) == "b.jpg"


def test_in_the_windows_viewer_on_a_playing_video_esc_to_the_grid_stops_the_video(qtbot, tmp_path):
    clip = make_clip(tmp_path / "a.mp4")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()
    make_surface_ready(viewer)
    wait_until_loaded(viewer.video_player.engine, clip)

    qtbot.keyClick(viewer, Qt.Key.Key_Escape)

    assert viewer.video_player.engine.path is None


def test_in_the_windows_viewer_with_the_tag_prompt_open_esc_closes_the_prompt_and_stays_in_the_viewer(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    viewer = stack.currentWidget()
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    qtbot.keyClick(viewer.focusWidget(), Qt.Key.Key_Escape)

    assert visible_tag_prompts(viewer) == []
    assert stack.currentWidget() is viewer


def test_on_the_windows_launch_screen_esc_quits_the_app(qtbot):
    window = Window(player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)

    qtbot.keyClick(window.findChild(QStackedWidget).currentWidget(), Qt.Key.Key_Escape)

    assert not window.isVisible()


def test_on_the_windows_launch_screen_esc_in_a_dropped_folders_slideshow_shows_that_folders_grid(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    drag_and_drop_onto(stack.currentWidget(), tmp_path)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.folder == tmp_path
    assert shown.currentIndex().data(Qt.ItemDataRole.DisplayRole) == "a.jpg"


def test_in_the_windows_grid_enter_on_a_file_starts_that_folders_slideshow_at_that_file(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    make_image(tmp_path / "c.jpg", "green")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == tmp_path / "b.jpg"


def test_in_the_windows_grid_enter_on_a_folder_opens_that_folders_grid_with_the_cursor_on_its_first_entry(qtbot, tmp_path):
    (tmp_path / "day1").mkdir()
    make_image(tmp_path / "day1" / "x.jpg", "red")
    make_image(tmp_path / "day1" / "y.jpg", "blue")
    make_image(tmp_path / "a.jpg", "green")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Left)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(TILE_ROLE).path == tmp_path / "day1" / "x.jpg"


def test_in_the_windows_grid_backspace_opens_the_parent_folders_grid_with_the_cursor_on_the_folder_just_left(qtbot, tmp_path):
    (tmp_path / "day1").mkdir()
    make_image(tmp_path / "day1" / "x.jpg", "red")
    make_image(tmp_path / "a.jpg", "green")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Left)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Backspace)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(TILE_ROLE).path == tmp_path / "day1"


def test_in_the_windows_grid_of_a_drives_mount_point_backspace_stays_on_that_grid(qtbot, tmp_path):
    drive = tmp_path / "drive"
    drive.mkdir()
    make_image(drive / "a.jpg", "red")
    window = Window(drive, player_options=SILENT, is_mount_point=lambda path: path == drive,
        ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Backspace)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(TILE_ROLE).path == drive / "a.jpg"


def test_in_the_windows_grid_esc_quits_the_app(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert not window.isVisible()


def test_in_the_windows_grid_f_toggles_fullscreen(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    was_fullscreen = window.isFullScreen()

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_F)

    assert window.isFullScreen() is not was_fullscreen


def test_in_the_windows_grid_f_twice_leaves_fullscreen_again(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    was_fullscreen = window.isFullScreen()

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_F)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_F)

    assert window.isFullScreen() is was_fullscreen


def test_dropping_a_folder_onto_the_windows_grid_starts_that_folders_slideshow(qtbot, tmp_path):
    viewed, dropped = make_folders(tmp_path, "viewed", "dropped")
    make_image(viewed / "a.jpg", "red")
    make_image(dropped / "x.jpg", "green")
    make_image(dropped / "y.jpg", "blue")
    window = Window(viewed, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    drag_and_drop_onto(stack.currentWidget().viewport(), dropped)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == dropped / "x.jpg"


def test_dropping_a_file_onto_the_windows_grid_starts_its_folders_slideshow_at_that_file(qtbot, tmp_path):
    viewed, dropped = make_folders(tmp_path, "viewed", "dropped")
    make_image(viewed / "a.jpg", "red")
    make_image(dropped / "x.jpg", "green")
    make_image(dropped / "y.jpg", "blue")
    window = Window(viewed, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    drag_and_drop_onto(stack.currentWidget().viewport(), dropped / "y.jpg")

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == dropped / "y.jpg"


def test_after_going_back_and_forth_between_grids_and_the_viewer_many_times_the_window_holds_only_the_grid_shown(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)

    for _ in range(5):
        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    assert window.findChildren(Grid) == [stack.currentWidget()]


def test_opening_a_file_from_the_windows_grid_letting_qt_process_deferred_deletions_then_esc_shows_the_grid_with_the_cursor_on_that_file(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(Qt.ItemDataRole.DisplayRole) == "b.jpg"


def shown_status_bar_texts(window):
    return [label.text() for bar in window.findChildren(StatusBar) for label in bar.findChildren(QLabel) if label.isVisible()]


def shown_texts_outside_the_status_bar(window):
    return [label.text() for label in window.findChildren(QLabel) if label.isVisible() and not window.status_bar.isAncestorOf(label)]


def window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach family")
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    return window, stack


def test_moving_the_windows_grid_cursor_onto_a_tagged_item_shows_its_own_tags_space_separated_in_the_status_bar(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    assert "beach family" in shown_status_bar_texts(window)


def test_moving_the_windows_grid_cursor_onto_an_item_tagged_beach_in_a_folder_tagged_holiday_shows_beach_followed_by_holiday_in_the_status_bar(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    library = Library.open(drive)
    library.enter(folder, "holiday")
    library.enter(folder / "IMG_2.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    shown = " ".join(shown_status_bar_texts(window)).split()
    assert "holiday" in shown
    assert shown.index("beach") < shown.index("holiday")


def test_in_the_windows_grid_status_bar_a_file_in_a_folder_tagged_zoo_inside_a_folder_tagged_apple_lists_its_inherited_tags_alphabetically_and_a_tag_both_folders_carry_once(qtbot, tmp_path):
    drive, outer = drive_with_a_tag_library_holding_one_image(tmp_path)
    inner = outer / "Zoo"
    inner.mkdir()
    make_image(inner / "IMG_1.png", "red")
    make_image(inner / "IMG_2.png", "blue")
    library = Library.open(drive)
    library.enter(outer, "apple both")
    library.enter(inner, "zoo both")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, inner)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    assert "apple both zoo" in shown_status_bar_texts(window)


def test_in_the_windows_grid_status_bar_an_inherited_tag_is_drawn_dimmer_than_an_own_tag(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    library = Library.open(drive)
    library.enter(folder, "holiday")
    library.enter(folder / "IMG_2.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    tag_labels = [label for label in window.status_bar.findChildren(QLabel) if label.isVisible() and ("beach" in label.text() or "holiday" in label.text())]
    left = min(label.geometry().left() for label in tag_labels)
    right = max(label.geometry().right() for label in tag_labels)
    image = window.status_bar.grab().toImage()

    def brightest_in(columns):
        return max(image.pixelColor(x, y).lightness() for x in columns for y in range(image.height()))
    width = right - left
    own_brightness = brightest_in(range(left, left + width // 4))  # "beach", shown first
    inherited_brightness = brightest_in(range(right - width // 3, right))  # "holiday", shown last
    assert own_brightness > 240
    assert inherited_brightness < own_brightness - 60


def test_pressing_t_in_the_windows_grid_on_a_file_tile_tagged_beach_family_opens_the_tag_prompt_showing_beach_family_above_its_empty_input(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_T)

    assert visible_tag_prompt_texts(window) == [""]
    assert "beach family" in shown_texts_outside_the_status_bar(window)


def test_pressing_t_in_the_windows_grid_on_a_read_only_drive_opens_no_tag_prompt_and_says_tags_cant_be_saved_here(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
        qtbot.addWidget(window)
        show_exposed(qtbot, window)
        stack = window.findChild(QStackedWidget)
        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_T)

    assert visible_tag_prompts(window) == []
    assert TAGS_CANT_BE_SAVED_HERE_TEXT in shown_status_bar_texts(window)


def window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder):
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Left)
    return window, stack


def enter_in_the_grids_tag_prompt(qtbot, window, stack, text):
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_T)
    [prompt] = visible_tag_prompts(window)
    qtbot.keyClicks(prompt, text)
    qtbot.keyClick(prompt, Qt.Key.Key_Return)


def test_pressing_t_in_the_windows_grid_on_a_folder_tile_tagged_beach_family_opens_the_tag_prompt_showing_beach_family_above_its_empty_input(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    [trip] = make_folders(folder, "trip")
    Library.open(drive).enter(trip, "beach family")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_T)

    assert visible_tag_prompt_texts(window) == [""]
    assert "beach family" in shown_texts_outside_the_status_bar(window)


def test_entering_beach_family_in_the_windows_grid_tag_prompt_on_a_folder_tile_saves_both_as_that_folders_own_tags_and_closes_the_prompt(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    [trip] = make_folders(folder, "trip")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "beach family")

    assert Library.open(drive).tags(trip) == ["beach", "family"]
    assert visible_tag_prompts(window) == []


def test_entering_minus_sunset_in_the_windows_grid_tag_prompt_removes_sunset_from_the_selected_items_own_tags(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    [trip] = make_folders(folder, "trip")
    Library.open(drive).enter(trip, "beach sunset")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "-sunset")

    assert Library.open(drive).tags(trip) == ["beach"]


def test_after_entering_beach_family_in_the_windows_grid_tag_prompt_the_selected_tile_shows_a_tag_badge_with_count_2(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_folders(folder, "trip")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "beach family")

    grid = stack.currentWidget()
    assert f"{TAG_BADGE}2" in painted_texts(grid, grid.currentIndex().row())


def test_after_entering_beach_family_in_the_windows_grid_tag_prompt_the_status_bar_shows_beach_family(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_folders(folder, "trip")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "beach family")

    assert "beach family" in shown_status_bar_texts(window)


def test_after_entering_beach_in_the_windows_grid_tag_prompt_on_a_folder_tile_enter_on_a_file_inside_it_shows_beach_in_the_viewers_tag_overlay(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    [trip] = make_folders(folder, "trip")
    make_image(trip / "IMG_1.png", "red")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    enter_in_the_grids_tag_prompt(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    viewer = stack.currentWidget()
    assert isinstance(viewer, Viewer)
    assert viewer.slideshow.current == trip / "IMG_1.png"
    assert shown_texts(viewer) == ["beach"]


def window_with_the_grids_tag_prompt_focused_on_a_drive_whose_library_has_beach(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    [trip] = make_folders(folder, "trip")
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_T)
    [prompt] = visible_tag_prompts(window)
    qtbot.waitUntil(prompt.hasFocus)
    return window, prompt


def suggestion_popup_after_typing(qtbot, prompt, text):
    qtbot.keyClicks(prompt, text)
    suggestions = prompt.completer().popup()
    qtbot.waitUntil(suggestions.isVisible)
    return suggestions


def test_typing_b_in_the_windows_grid_tag_prompt_on_a_drive_whose_library_has_beach_lists_beach_in_the_suggestion_popup(qtbot, tmp_path):
    window, prompt = window_with_the_grids_tag_prompt_focused_on_a_drive_whose_library_has_beach(qtbot, tmp_path)

    suggestions = suggestion_popup_after_typing(qtbot, prompt, "b")

    assert listed(suggestions) == ["beach"]


def test_when_saving_from_the_windows_grid_tag_prompt_fails_because_the_drive_has_gone_away_the_prompt_stays_open_with_its_text_and_the_status_bar_says_it_couldnt_save_tags(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    def enter_on_an_unplugged_drive(self, path, text):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(Library, "enter", enter_on_an_unplugged_drive)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "beach")

    assert visible_tag_prompt_texts(window) == ["beach"]
    assert "Couldn't save tags — is the drive still connected?" in shown_status_bar_texts(window)


def test_esc_with_the_suggestion_popup_open_in_the_windows_grid_tag_prompt_closes_only_the_popup_leaving_the_prompt_open_with_its_text(qtbot, tmp_path):
    window, prompt = window_with_the_grids_tag_prompt_focused_on_a_drive_whose_library_has_beach(qtbot, tmp_path)
    suggestions = suggestion_popup_after_typing(qtbot, prompt, "b")

    qtbot.keyClick(suggestions, Qt.Key.Key_Escape)

    assert (suggestions.isVisible(), visible_tag_prompt_texts(window)) == (False, ["b"])


def test_esc_with_no_suggestion_popup_in_the_windows_grid_tag_prompt_closes_the_prompt_and_keeps_the_app_running_with_the_grid_shown(qtbot, tmp_path):
    window, prompt = window_with_the_grids_tag_prompt_focused_on_a_drive_whose_library_has_beach(qtbot, tmp_path)

    qtbot.keyClick(prompt, Qt.Key.Key_Escape)

    shown = window.findChild(QStackedWidget).currentWidget()
    assert (visible_tag_prompts(window), window.isVisible(), isinstance(shown, Grid)) == ([], True, True)


def test_while_the_windows_grid_tag_prompt_is_open_arrows_backspace_plus_and_minus_leave_the_grids_cursor_folder_and_tile_size_unchanged(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_folders(folder, "trip")
    for n in range(2, 40):
        make_image(folder / f"IMG_{n:02}.png", "blue")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    grid = stack.currentWidget()
    before = (grid.currentIndex().row(), grid.folder, grid.gridSize())
    qtbot.keyClick(grid, Qt.Key.Key_T)
    [prompt] = visible_tag_prompts(window)
    qtbot.waitUntil(prompt.hasFocus)

    for key in (Qt.Key.Key_Up, Qt.Key.Key_Right, Qt.Key.Key_Left, Qt.Key.Key_Down, Qt.Key.Key_Plus, Qt.Key.Key_Minus, Qt.Key.Key_Backspace):
        qtbot.keyClick(prompt, key)

    assert (stack.currentWidget(), (grid.currentIndex().row(), grid.folder, grid.gridSize())) == (grid, before)


def test_after_the_windows_grid_tag_prompt_closes_arrows_move_the_grids_cursor_again(qtbot, tmp_path):
    window, prompt = window_with_the_grids_tag_prompt_focused_on_a_drive_whose_library_has_beach(qtbot, tmp_path)
    grid = window.findChild(QStackedWidget).currentWidget()
    qtbot.keyClick(prompt, Qt.Key.Key_Escape)

    qtbot.keyClick(window.focusWidget(), Qt.Key.Key_Right)

    assert grid.currentIndex().row() == 1


def test_the_windows_grid_tag_prompt_sits_at_the_bottom_centre_just_above_the_status_bar_entirely_inside_the_window_also_after_a_resize(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_T)

    resize_and_wait(qtbot, window, 900, 700)

    [prompt] = visible_tag_prompts(window)
    frame = frame_in(window, prompt)
    assert window.rect().contains(frame)
    assert abs(frame.center().x() - window.rect().center().x()) <= 1
    assert frame.bottom() == window.status_bar.geometry().top() - 1


def test_moving_the_windows_grid_cursor_onto_an_untagged_item_shows_no_tags_in_the_status_bar(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Left)

    shown = shown_status_bar_texts(window)
    assert "beach family" not in shown
    assert "" not in shown


def test_the_library_status_of_a_read_only_drive_stays_visible_in_the_status_bar_while_the_windows_grid_is_shown(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
        qtbot.addWidget(window)
        show_exposed(qtbot, window)
        stack = window.findChild(QStackedWidget)

        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert isinstance(stack.currentWidget(), Grid)
    assert READ_ONLY_STATUS_TEXT in shown_status_bar_texts(window)


def test_a_backup_failure_shown_in_the_windows_viewer_stays_visible_in_the_status_bar_after_esc_shows_the_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    (backup_root / Library.open(drive).drive_id / "drive.json").mkdir(parents=True)
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False, backup_root=backup_root)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert isinstance(stack.currentWidget(), Grid)
    assert BACKUP_FAILED_TEXT.format(os.strerror(errno.EISDIR)) in shown_status_bar_texts(window)


def test_going_from_the_windows_viewer_to_the_grid_and_back_on_the_same_drive_makes_no_new_backup(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    ticks = iter(datetime(2026, 10, 10, 12, 0, second, tzinfo=timezone.utc) for second in range(60))
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False, backup_root=backup_root, backup_clock=lambda: next(ticks))
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    enter_in_tag_prompt(qtbot, stack.currentWidget(), "sunset")
    backups_before = sorted((backup_root / Library.open(drive).drive_id).glob("tags-*.db"))

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert isinstance(stack.currentWidget(), Viewer)
    assert sorted((backup_root / Library.open(drive).drive_id).glob("tags-*.db")) == backups_before


def test_going_from_the_windows_viewer_to_the_grid_and_back_on_the_same_drive_does_not_ask_again_to_create_its_library(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    asked = []
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=decline_noting_the_question_in(asked))
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert isinstance(stack.currentWidget(), Viewer)
    assert asked == [CREATE_LIBRARY_QUESTION.format(drive.name)]


def test_going_from_the_windows_viewer_to_the_grid_and_back_on_a_drive_whose_tags_db_is_damaged_after_declining_the_restore_asks_no_restore_question_again(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    taken_at = datetime(2026, 10, 9, 15, 30, tzinfo=timezone.utc)
    back_up(Library.open(drive), backup_root, clock=lambda: taken_at)
    overwrite_tags_db_with_garbage(drive)
    asked = []
    window = Window(
        folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False,
        backup_root=backup_root, ask_to_restore_library=decline_noting_the_question_in(asked),
    )
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert isinstance(stack.currentWidget(), Viewer)
    assert asked == [RESTORE_LIBRARY_QUESTION.format(drive.name, taken_at.astimezone())]


def test_opening_a_file_from_the_windows_grid_takes_the_grids_selected_item_tags_off_the_status_bar(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert isinstance(stack.currentWidget(), Viewer)
    assert "beach family" not in shown_status_bar_texts(window)


def test_scrolled_to_the_end_the_windows_grid_keeps_its_last_row_of_tiles_just_above_the_status_bar(qtbot, tmp_path):
    for name in "abcde":
        make_image(tmp_path / f"{name}.jpg", "red")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    window.resize(400, 330)
    window.show()
    qtbot.waitExposed(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    grid = stack.currentWidget()

    grid.scrollToBottom()

    last_tile = grid.visualRect(grid.model().index(grid.model().rowCount() - 1, 0))
    last_tile_bottom = grid.viewport().mapTo(window, last_tile.bottomLeft()).y()
    status_bar_top = window.status_bar.geometry().top()
    assert status_bar_top - grid.frameWidth() - grid.spacing() - 1 <= last_tile_bottom < status_bar_top


def test_after_tagging_a_file_in_the_windows_viewer_esc_shows_its_grid_tile_with_the_updated_tag_badge(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    enter_in_tag_prompt(qtbot, stack.currentWidget(), "beach family")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    grid = stack.currentWidget()
    assert isinstance(grid, Grid)
    assert f"{TAG_BADGE}2" in painted_texts(grid, grid.currentIndex().row())


def test_closing_the_window_shuts_down_its_viewers_video_player_and_leaves_a_backup_of_the_open_library_holding_the_entered_tag(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    clip = make_clip(folder / "IMG_0.mp4")
    backup_root = tmp_path / "backups"
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False, backup_root=backup_root)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    wait_until_loaded(engine, clip)
    enter_in_tag_prompt(qtbot, viewer, "sunset")

    window.close()

    assert engine.handle is None
    assert tags_in_newest_backup(backup_root, drive, tmp_path / "restored", "Photos/IMG_0.mp4") == ["sunset"]


def test_entering_a_subfolder_from_the_windows_grid_shows_tag_badges_for_its_tagged_items(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    (folder / "day1").mkdir()
    make_image(folder / "day1" / "x.png", "blue")
    Library.open(drive).enter(folder / "day1" / "x.png", "beach family")
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Left)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    grid = stack.currentWidget()
    assert grid.folder == folder / "day1"
    assert f"{TAG_BADGE}2" in painted_texts(grid, 0)


def test_pressing_enter_in_the_windows_grid_on_a_folder_whose_first_item_is_tagged_beach_family_shows_beach_family_in_the_status_bar_before_any_cursor_move(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    (folder / "day1").mkdir()
    make_image(folder / "day1" / "x.png", "blue")
    Library.open(drive).enter(folder / "day1" / "x.png", "beach family")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert stack.currentWidget().folder == folder / "day1"
    assert "beach family" in shown_status_bar_texts(window)


def test_pressing_enter_in_the_windows_grid_on_a_folder_tagged_beach_family_whose_first_item_is_untagged_shows_beach_family_only_dimmed_as_inherited_not_as_the_items_own_tags(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    (folder / "day1").mkdir()
    make_image(folder / "day1" / "x.png", "blue")
    Library.open(drive).enter(folder / "day1", "beach family")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert stack.currentWidget().folder == folder / "day1"
    image = window.status_bar.grab().toImage()
    tag_labels = [label for label in window.status_bar.findChildren(QLabel) if label.isVisible() and "beach" in label.text()]
    brightest = max(image.pixelColor(x, y).lightness() for label in tag_labels for x in range(label.geometry().left(), label.geometry().right()) for y in range(image.height()))
    assert brightest < 200  # an own tag is drawn white; an inherited one well below it


def test_pressing_backspace_in_the_windows_grid_back_to_a_folder_whose_cursor_lands_on_a_subfolder_tagged_beach_family_shows_beach_family_in_the_status_bar_before_any_cursor_move(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    (folder / "day1").mkdir()
    make_image(folder / "day1" / "x.png", "blue")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    Library.open(drive).enter(folder / "day1", "beach family")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Backspace)

    assert stack.currentWidget().currentIndex().data(TILE_ROLE).path == folder / "day1"
    assert "beach family" in shown_status_bar_texts(window)
