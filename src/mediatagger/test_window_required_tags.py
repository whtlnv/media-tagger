import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget

from mediatagger.drive_config import CONFIG_CANT_BE_READ_TEXT, CONFIG_FILE
from mediatagger.grid import MISSING_BADGE, Grid
from mediatagger.test_grid_required_tags import missing_badge
from mediatagger.test_viewer import SILENT, show_exposed
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
from mediatagger.test_viewer_open import drag_and_drop_onto
from mediatagger.test_window import shown_status_bar_texts, window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.window import Window


def write_config(drive, required_roots):
    (drive / CONFIG_FILE).write_text(json.dumps({"requiredRoots": required_roots}), encoding="utf-8")


def test_opening_a_folder_on_a_drive_whose_config_names_two_roots_marks_its_untagged_files_tile_as_missing_both(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_config(drive, ["type:", "size:"])

    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    assert missing_badge(stack.currentWidget(), 0) == f"{MISSING_BADGE}2"


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
    assert (stack.currentWidget().folder, missing_badge(stack.currentWidget(), 0)) == (second_folder, f"{MISSING_BADGE}1")
