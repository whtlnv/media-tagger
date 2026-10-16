import errno
import os
import sqlite3
from datetime import datetime, timezone

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget

from mediatagger.drive_session import BACKUP_FAILED_TEXT
from mediatagger.grid import TAG_BADGE, TILE_ROLE
from mediatagger.library import Library
from mediatagger.status_bar import (NO_SUCH_TAG_TEXT, RENAME_LEADING_DASH_TEXT, RENAME_NEEDS_TWO_TAGS_TEXT, RENAME_TO_SAME_TAG_TEXT,
    TAGS_CANT_BE_SAVED_HERE_TEXT)
from mediatagger.test_grid import painted_texts
from mediatagger.test_tag_prompt import listed
from mediatagger.test_viewer import SILENT, show_exposed
from mediatagger.test_viewer_backup import tags_in_newest_backup
from mediatagger.test_viewer_library import (drive_with_a_tag_library_holding_one_image, drive_without_a_tag_library_holding_one_image, made_read_only,
    visible_tag_prompts)
from mediatagger.test_window import (enter_in_the_grids_tag_prompt, shown_status_bar_texts, shown_texts_outside_the_status_bar, suggestion_popup_after_typing,
    window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family, window_showing_the_grid_with_its_cursor_on_its_first_tile)
from mediatagger.window import Window


def opened_rename_prompt(qtbot, window, grid):
    qtbot.keyClick(grid, Qt.Key.Key_N)
    [prompt] = visible_tag_prompts(window)
    return prompt


def rename_prompt_after_typing(qtbot, window, grid, text):
    prompt = opened_rename_prompt(qtbot, window, grid)
    qtbot.keyClicks(prompt, text)
    return prompt


def test_pressing_n_in_the_windows_folder_grid_opens_one_empty_prompt_labelled_rename_tag_styled_like_the_tag_prompt(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_N)

    [prompt] = visible_tag_prompts(window)
    assert prompt.text() == ""
    assert prompt.styleSheet() == window.tag_prompt.input.styleSheet()
    assert "Rename tag:" in shown_texts_outside_the_status_bar(window)


def test_esc_in_the_windows_rename_prompt_after_typing_beach_places_beach_closes_only_the_prompt_staying_in_the_grid_and_leaves_the_item_tagged_beach_family(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    grid = stack.currentWidget()
    prompt = rename_prompt_after_typing(qtbot, window, grid, "beach places:beach")

    qtbot.keyClick(prompt, Qt.Key.Key_Escape)

    assert window.isVisible()
    assert stack.currentWidget() is grid
    assert visible_tag_prompts(window) == []
    assert "Rename tag:" not in shown_texts_outside_the_status_bar(window)
    drive = tmp_path / "MEDIATAGGER"
    assert Library.open(drive).tags(drive / "Photos" / "IMG_2.png") == ["beach", "family"]


def test_enter_on_beach_places_beach_in_the_windows_rename_prompt_renames_the_tag_in_the_drives_library_and_the_status_bar_says_how_many_items_it_renamed(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach places:beach")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    drive = tmp_path / "MEDIATAGGER"
    assert Library.open(drive).tags(drive / "Photos" / "IMG_2.png") == ["family", "places:beach"]
    assert "Renamed beach → places:beach on 1 item" in shown_status_bar_texts(window)


def test_enter_on_beach_places_beach_in_the_windows_rename_prompt_with_a_photo_and_its_folder_tagged_beach_says_on_2_items(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    library.enter(folder / "IMG_1.png", "beach")
    library.enter(folder, "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach places:beach")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    assert "Renamed beach → places:beach on 2 items" in shown_status_bar_texts(window)


def test_enter_on_capitalised_beach_places_beach_in_the_windows_rename_prompt_renames_beach_to_places_beach_lowercased(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "Beach Places:Beach")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    drive = tmp_path / "MEDIATAGGER"
    assert Library.open(drive).tags(drive / "Photos" / "IMG_2.png") == ["family", "places:beach"]
    assert "Renamed beach → places:beach on 1 item" in shown_status_bar_texts(window)


def test_after_enter_on_beach_family_in_the_windows_rename_prompt_the_open_grids_tile_tagged_beach_family_shows_a_tag_badge_with_count_1(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    grid = stack.currentWidget()
    prompt = rename_prompt_after_typing(qtbot, window, grid, "beach family")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    [row] = [row for row in range(grid.model().rowCount()) if grid.model().index(row, 0).data(TILE_ROLE).path.name == "IMG_2.png"]
    assert f"{TAG_BADGE}1" in painted_texts(grid, row)


def test_after_enter_on_beach_places_beach_in_the_windows_rename_prompt_the_open_grids_video_with_beach_and_places_beach_moments_a_half_second_apart_shows_a_moments_badge_reading_1(qtbot, tmp_path):
    from mediatagger.grid import MOMENTS_BADGE
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    (folder / "IMG_2.mp4").touch()
    library = Library.open(drive)
    library.add_chapter(folder / "IMG_2.mp4", "places:beach", 12.0)
    library.add_chapter(folder / "IMG_2.mp4", "beach", 12.5)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    grid = stack.currentWidget()
    prompt = rename_prompt_after_typing(qtbot, window, grid, "beach places:beach")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    [row] = [row for row in range(grid.model().rowCount()) if grid.model().index(row, 0).data(TILE_ROLE).path.name == "IMG_2.mp4"]
    assert f"{MOMENTS_BADGE} 1" in painted_texts(grid, row)


def test_after_enter_on_beach_places_beach_in_the_windows_rename_prompt_with_the_grids_cursor_on_the_item_tagged_beach_family_the_status_bar_shows_family_places_beach(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    grid = stack.currentWidget()
    qtbot.keyClick(grid, Qt.Key.Key_Right)
    prompt = rename_prompt_after_typing(qtbot, window, grid, "beach places:beach")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    assert "family places:beach" in shown_status_bar_texts(window)


def test_after_enter_on_a_rename_whose_old_tag_no_item_has_the_windows_rename_prompt_stays_open_with_what_was_typed(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "sunset places:sunset")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    assert [prompt.text() for prompt in visible_tag_prompts(window)] == ["sunset places:sunset"]


def test_enter_on_a_rename_in_the_windows_rename_prompt_with_no_library_open_says_tags_cant_be_saved_here(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach places:beach")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    assert TAGS_CANT_BE_SAVED_HERE_TEXT in shown_status_bar_texts(window)


def test_enter_on_a_rename_in_the_windows_rename_prompt_on_a_read_only_drive_says_tags_cant_be_saved_here(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    with made_read_only(drive):
        window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
        prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach places:beach")

        qtbot.keyClick(prompt, Qt.Key.Key_Return)

    assert TAGS_CANT_BE_SAVED_HERE_TEXT in shown_status_bar_texts(window)


@pytest.mark.parametrize(("typed", "message"), [
    ("sunset places:sunset", NO_SUCH_TAG_TEXT.format("sunset")),
    ("beach", RENAME_NEEDS_TWO_TAGS_TEXT),
    ("beach sea shore", RENAME_NEEDS_TWO_TAGS_TEXT),
    ("beach Beach", RENAME_TO_SAME_TAG_TEXT),
    ("-beach places", RENAME_LEADING_DASH_TEXT),
    ("beach -places", RENAME_LEADING_DASH_TEXT),
], ids=["old tag no item has", "a single word", "three words", "a tag to itself", "old name starting with a dash", "new name starting with a dash"])
def test_enter_on_a_rejected_rename_in_the_windows_rename_prompt_says_why_in_the_status_bar_and_changes_nothing(qtbot, tmp_path, typed, message):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), typed)

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    drive = tmp_path / "MEDIATAGGER"
    assert Library.open(drive).tags(drive / "Photos" / "IMG_2.png") == ["beach", "family"]
    assert message in shown_status_bar_texts(window)


def test_after_enter_applies_a_rename_in_the_windows_rename_prompt_the_prompt_closes_and_arrows_move_the_grids_cursor_again(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    grid = stack.currentWidget()
    prompt = rename_prompt_after_typing(qtbot, window, grid, "beach places:beach")
    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    qtbot.keyClick(window.focusWidget(), Qt.Key.Key_Right)

    assert visible_tag_prompts(window) == []
    assert "Rename tag:" not in shown_texts_outside_the_status_bar(window)
    assert stack.currentWidget() is grid
    assert grid.currentIndex().row() == 1


def test_enter_on_beach_places_beach_in_the_windows_rename_prompt_backs_up_the_library_first_so_the_newest_backup_still_holds_beach(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    ticks = iter(datetime(2026, 10, 16, 12, 0, second, tzinfo=timezone.utc) for second in range(60))
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False, backup_root=backup_root, backup_clock=lambda: next(ticks))
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    enter_in_the_grids_tag_prompt(qtbot, window, stack, "beach")
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach places:beach")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    assert Library.open(drive).tags(folder / "IMG_1.png") == ["places:beach"]
    assert tags_in_newest_backup(backup_root, drive, tmp_path / "restored", "Photos/IMG_1.png") == ["beach"]


def test_enter_on_beach_places_beach_in_the_windows_rename_prompt_when_the_backup_fails_leaves_beach_shows_the_failure_and_keeps_the_prompt_open(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    backup_root = tmp_path / "backups"
    (backup_root / Library.open(drive).drive_id / "drive.json").mkdir(parents=True)  # a directory where the backup writes a file
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False, backup_root=backup_root)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach places:beach")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    assert Library.open(drive).tags(folder / "IMG_1.png") == ["beach"]
    assert BACKUP_FAILED_TEXT.format(os.strerror(errno.EISDIR)) in shown_status_bar_texts(window)
    assert not [text for text in shown_status_bar_texts(window) if text.startswith("Renamed")]
    assert [prompt.text() for prompt in visible_tag_prompts(window)] == ["beach places:beach"]


@pytest.mark.parametrize("drive_error", [sqlite3.OperationalError("disk I/O error"), OSError(5, "Input/output error")], ids=["sqlite_error", "os_error"])
def test_when_a_rename_in_the_windows_rename_prompt_fails_with_a_drive_error_the_prompt_stays_open_with_its_text_and_the_status_bar_says_it_couldnt_save_tags(qtbot, tmp_path, monkeypatch, drive_error):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach places:beach")

    def rename_on_an_unplugged_drive(self, old, new):
        raise drive_error

    monkeypatch.setattr(Library, "rename_tag", rename_on_an_unplugged_drive)

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    assert [prompt.text() for prompt in visible_tag_prompts(window)] == ["beach places:beach"]
    assert "Couldn't save tags — is the drive still connected?" in shown_status_bar_texts(window)


def test_after_a_rename_in_the_windows_rename_prompt_fails_with_a_drive_error_enter_again_once_the_drive_is_back_renames_and_takes_the_couldnt_save_message_off(qtbot, tmp_path, monkeypatch):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach places:beach")

    def rename_on_an_unplugged_drive(self, old, new):
        raise sqlite3.OperationalError("disk I/O error")

    with monkeypatch.context() as unplugged:
        unplugged.setattr(Library, "rename_tag", rename_on_an_unplugged_drive)
        qtbot.keyClick(prompt, Qt.Key.Key_Return)

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    drive = tmp_path / "MEDIATAGGER"
    assert Library.open(drive).tags(drive / "Photos" / "IMG_2.png") == ["family", "places:beach"]
    assert "Couldn't save tags — is the drive still connected?" not in shown_status_bar_texts(window)


def test_enter_on_a_rename_whose_old_tag_no_item_has_in_the_windows_rename_prompt_makes_no_backup_so_the_newest_backup_is_still_the_one_from_opening(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    ticks = iter(datetime(2026, 10, 16, 12, 0, second, tzinfo=timezone.utc) for second in range(60))
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False, backup_root=backup_root, backup_clock=lambda: next(ticks))
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    enter_in_the_grids_tag_prompt(qtbot, window, stack, "beach")
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "sunset places:sunset")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    assert tags_in_newest_backup(backup_root, drive, tmp_path / "restored", "Photos/IMG_1.png") == []


def test_typing_b_as_the_first_word_in_the_windows_rename_prompt_on_a_drive_whose_library_has_beach_family_lists_beach_in_the_suggestion_popup(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = opened_rename_prompt(qtbot, window, stack.currentWidget())
    qtbot.waitUntil(prompt.hasFocus)

    suggestions = suggestion_popup_after_typing(qtbot, prompt, "b")

    assert listed(suggestions) == ["beach"]


def test_typing_beach_f_as_the_second_word_in_the_windows_rename_prompt_on_a_drive_whose_library_has_beach_family_lists_family_in_the_suggestion_popup(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = opened_rename_prompt(qtbot, window, stack.currentWidget())
    qtbot.waitUntil(prompt.hasFocus)

    suggestions = suggestion_popup_after_typing(qtbot, prompt, "beach f")

    assert listed(suggestions) == ["family"]


def test_typing_capital_b_in_the_windows_rename_prompt_lists_beach_in_a_suggestion_popup_styled_like_the_tag_prompts(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = opened_rename_prompt(qtbot, window, stack.currentWidget())
    qtbot.waitUntil(prompt.hasFocus)

    suggestions = suggestion_popup_after_typing(qtbot, prompt, "B")

    assert listed(suggestions) == ["beach"]
    assert suggestions.styleSheet() == window.tag_prompt.input.completer().popup().styleSheet()


def test_up_in_the_windows_rename_prompt_reopened_after_applying_beach_places_beach_recalls_beach_places_beach(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach places:beach")
    qtbot.keyClick(prompt, Qt.Key.Key_Return)
    prompt = opened_rename_prompt(qtbot, window, window.focusWidget())

    qtbot.keyClick(prompt, Qt.Key.Key_Up)

    assert prompt.text() == "beach places:beach"


def test_up_up_down_in_the_windows_rename_prompt_after_applying_beach_places_beach_then_family_people_family_recalls_older_then_newer(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    for rename in ("beach places:beach", "family people:family"):
        prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), rename)
        qtbot.keyClick(prompt, Qt.Key.Key_Return)
    prompt = opened_rename_prompt(qtbot, window, stack.currentWidget())

    recalled = []
    for key in (Qt.Key.Key_Up, Qt.Key.Key_Up, Qt.Key.Key_Down):
        qtbot.keyClick(prompt, key)
        recalled.append(prompt.text())

    assert recalled == ["family people:family", "beach places:beach", "family people:family"]


def test_up_in_the_windows_rename_prompt_after_applying_beach_places_beach_then_entering_a_rename_of_an_unknown_tag_recalls_beach_places_beach(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    for rename in ("beach places:beach", "nosuch other"):
        prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), rename)
        qtbot.keyClick(prompt, Qt.Key.Key_Return)
    qtbot.keyClick(prompt, Qt.Key.Key_Escape)
    prompt = opened_rename_prompt(qtbot, window, stack.currentWidget())

    qtbot.keyClick(prompt, Qt.Key.Key_Up)

    assert prompt.text() == "beach places:beach"


def test_up_in_the_rename_prompt_of_a_window_opened_after_one_that_applied_beach_places_beach_was_closed_recalls_beach_places_beach(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach places:beach")
    qtbot.keyClick(prompt, Qt.Key.Key_Return)
    window.close()
    reopened, reopened_stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path / "reopened")
    prompt = opened_rename_prompt(qtbot, reopened, reopened_stack.currentWidget())

    qtbot.keyClick(prompt, Qt.Key.Key_Up)

    assert prompt.text() == "beach places:beach"
