from PySide6.QtCore import Qt

from mediatagger.grid_filter import MISSING_TAGS, WITH_TAGS
from mediatagger.library import Library
from mediatagger.test_grid_filter import shown_tile_names
from mediatagger.test_viewer import make_image
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
from mediatagger.test_viewer_open import make_folders
from mediatagger.test_window import window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.test_window_required_tags import write_config
from mediatagger.test_window_search import search_for


def test_a_filter_chosen_in_one_folders_grid_applies_to_the_next_folder_opened_in_the_same_window(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    [trip] = make_folders(folder, "Trip")
    make_image(trip / "IMG_2.png", "blue")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    window.grid_filter.choose(WITH_TAGS)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert (stack.currentWidget().folder, shown_tile_names(stack.currentWidget())) == (trip, [])


def test_a_new_window_starts_with_no_filter_whatever_was_chosen_in_an_earlier_window(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    earlier, _ = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    earlier.grid_filter.choose(WITH_TAGS)
    earlier.close()

    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    assert (window.grid_filter.active, shown_tile_names(stack.currentWidget())) == (None, ["IMG_1.png"])


def test_under_a_filter_a_search_results_grid_hides_result_files_that_dont_match(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    library = Library.open(drive)
    library.enter(folder / "IMG_1.png", "beach type:photo")
    library.enter(folder / "IMG_2.png", "beach")
    write_config(drive, ["type:"])
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    window.grid_filter.choose(MISSING_TAGS)

    search_for(qtbot, window, stack, "beach")

    assert shown_tile_names(stack.currentWidget()) == ["IMG_2.png"]
