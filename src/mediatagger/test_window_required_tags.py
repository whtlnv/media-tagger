import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget

from mediatagger.drive_config import CONFIG_CANT_BE_READ_TEXT, CONFIG_FILE
from mediatagger.grid import MISSING_ROOTS_BADGE, TAG_BADGE, Grid
from mediatagger.library import Library
from mediatagger.test_grid import painted_texts
from mediatagger.test_grid_required_tags import missing_badge
from mediatagger.test_viewer import SILENT, show_exposed
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, visible_tag_prompts
from mediatagger.test_viewer_open import drag_and_drop_onto
from mediatagger.test_window import enter_in_the_grids_tag_prompt, shown_status_bar_texts, window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.test_window_search import search_for
from mediatagger.window import Window


def write_config(drive, required_roots):
    (drive / CONFIG_FILE).write_text(json.dumps({"requiredRoots": required_roots}), encoding="utf-8")


def test_opening_a_folder_on_a_drive_whose_config_names_two_roots_marks_its_untagged_files_tile_as_missing_both(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_config(drive, ["type:", "size:"])

    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    assert missing_badge(stack.currentWidget(), 0) == f"{MISSING_ROOTS_BADGE}2"


def test_opening_a_folder_on_a_drive_with_no_config_marks_no_tile(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)

    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    assert missing_badge(stack.currentWidget(), 0) is None


def test_opening_a_drive_whose_config_isnt_valid_json_says_so_in_the_status_bar_marks_no_tile_and_still_shows_the_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    (drive / CONFIG_FILE).write_text('{"requiredRoots": ["type:"', encoding="utf-8")

    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    assert (isinstance(stack.currentWidget(), Grid), missing_badge(stack.currentWidget(), 0)) == (True, None)
    assert CONFIG_CANT_BE_READ_TEXT in shown_status_bar_texts(window)


def test_after_a_drive_with_an_invalid_config_dropping_a_folder_of_a_drive_with_a_valid_one_clears_the_problem_and_marks_by_the_new_config(qtbot, tmp_path):
    first_drive, first_folder = drive_with_a_tag_library_holding_one_image(tmp_path / "first")
    (first_drive / CONFIG_FILE).write_text("{not json", encoding="utf-8")
    second_drive, second_folder = drive_with_a_tag_library_holding_one_image(tmp_path / "second")
    write_config(second_drive, ["type:"])
    window = Window(first_folder, player_options=SILENT, is_mount_point=lambda path: path in (first_drive, second_drive),
        ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    drag_and_drop_onto(stack.currentWidget().viewport(), second_folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert CONFIG_CANT_BE_READ_TEXT not in shown_status_bar_texts(window)
    assert (stack.currentWidget().folder, missing_badge(stack.currentWidget(), 0)) == (second_folder, f"{MISSING_ROOTS_BADGE}1")


def test_tagging_the_grid_cursors_file_with_a_missing_root_updates_its_mark_at_once(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_config(drive, ["type:", "size:"])
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "type:photo")
    after_type = missing_badge(stack.currentWidget(), 0)
    enter_in_the_grids_tag_prompt(qtbot, window, stack, "size:big")

    assert (after_type, missing_badge(stack.currentWidget(), 0)) == (f"{MISSING_ROOTS_BADGE}1", None)


def test_tagging_a_result_file_with_a_missing_root_in_the_results_grid_updates_its_mark_at_once(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_config(drive, ["type:", "size:"])
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    before = missing_badge(stack.currentWidget(), 0)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "type:photo")

    assert (before, missing_badge(stack.currentWidget(), 0)) == (f"{MISSING_ROOTS_BADGE}2", f"{MISSING_ROOTS_BADGE}1")


def test_tagging_a_file_in_a_slideshow_opened_from_results_then_esc_back_to_them_shows_its_new_mark_and_tag_count(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_config(drive, ["type:", "size:"])
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    results = stack.currentWidget()
    qtbot.keyClick(results, Qt.Key.Key_Return)

    enter_in_tag_prompt(qtbot, stack.currentWidget(), "type:photo")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert stack.currentWidget() is results
    assert (missing_badge(results, 0), f"{TAG_BADGE}2" in painted_texts(results, 0)) == (f"{MISSING_ROOTS_BADGE}1", True)


def test_after_enter_on_photo_type_photo_in_the_windows_rename_prompt_the_open_grids_file_tagged_photo_on_a_drive_requiring_type_shows_no_missing_badge(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_config(drive, ["type:"])
    Library.open(drive).enter(folder / "IMG_1.png", "photo")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    grid = stack.currentWidget()
    before = missing_badge(grid, 0)
    qtbot.keyClick(grid, Qt.Key.Key_N)
    [prompt] = visible_tag_prompts(window)
    qtbot.keyClicks(prompt, "photo type:photo")

    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    assert (before, missing_badge(grid, 0)) == (f"{MISSING_ROOTS_BADGE}1", None)


def test_opening_and_browsing_a_drive_with_a_config_leaves_its_root_and_its_config_untouched(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_config(drive, ["type:", "size:"])
    config = drive / CONFIG_FILE
    before = (sorted(path.name for path in drive.iterdir()), config.read_bytes(), config.stat().st_mtime_ns)

    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    window.close()

    assert (sorted(path.name for path in drive.iterdir()), config.read_bytes(), config.stat().st_mtime_ns) == before
