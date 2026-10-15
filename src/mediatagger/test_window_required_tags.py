import json

from mediatagger.drive_config import CONFIG_FILE
from mediatagger.grid import MISSING_BADGE
from mediatagger.test_grid_required_tags import missing_badge
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
from mediatagger.test_window import window_showing_the_grid_with_its_cursor_on_its_first_tile


def write_config(drive, required_roots):
    (drive / CONFIG_FILE).write_text(json.dumps({"requiredRoots": required_roots}), encoding="utf-8")


def test_opening_a_folder_on_a_drive_whose_config_names_two_roots_marks_its_untagged_files_tile_as_missing_both(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_config(drive, ["type:", "size:"])

    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    assert missing_badge(stack.currentWidget(), 0) == f"{MISSING_BADGE}2"
