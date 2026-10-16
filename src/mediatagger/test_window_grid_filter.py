from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from mediatagger.grid_filter import MISSING_TAGS, NO_TAGS, WITH_TAGS, FilterButton
from mediatagger.library import Library
from mediatagger.test_grid_filter import popped_up_menu, shown_tile_names
from mediatagger.test_viewer import make_image
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt
from mediatagger.test_viewer_open import make_folders
from mediatagger.test_window import enter_in_the_grids_tag_prompt, shown_status_bar_texts, window_showing_the_grid_with_its_cursor_on_its_first_tile
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


def test_under_with_tags_removing_a_files_last_own_tag_from_the_grids_tag_prompt_hides_it_at_once(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    window.grid_filter.choose(WITH_TAGS)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "-beach")

    assert shown_tile_names(stack.currentWidget()) == []


def test_under_no_tags_adding_a_tag_to_a_shown_file_from_the_grids_tag_prompt_hides_it_at_once(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    window.grid_filter.choose(NO_TAGS)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "beach")

    assert shown_tile_names(stack.currentWidget()) == []


def test_under_no_tags_adding_a_tag_to_a_files_folder_leaves_the_file_shown(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    [trip] = make_folders(folder, "Trip")
    make_image(trip / "IMG_2.png", "blue")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    window.grid_filter.choose(NO_TAGS)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "holiday")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert (stack.currentWidget().folder, shown_tile_names(stack.currentWidget())) == (trip, ["IMG_2.png"])


def test_choosing_a_filter_that_hides_every_file_of_a_folder_with_no_subfolders_leaves_no_cursor_and_clears_the_status_bars_tags(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    shown_before = shown_status_bar_texts(window)

    window.grid_filter.choose(NO_TAGS)

    assert ("beach" in shown_before, stack.currentWidget().currentIndex().isValid(), "beach" in shown_status_bar_texts(window)) == (True, False, False)


def cursor_name(stack):
    return stack.currentWidget().currentIndex().data(Qt.ItemDataRole.DisplayRole)


def test_opening_a_folder_whose_first_tile_is_hidden_by_the_filter_puts_the_cursor_on_the_first_shown_tile(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    [trip] = make_folders(folder, "Trip")
    make_image(trip / "IMG_2.png", "blue")
    make_image(trip / "IMG_3.png", "green")
    Library.open(drive).enter(trip / "IMG_3.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    window.grid_filter.choose(WITH_TAGS)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert cursor_name(stack) == "IMG_3.png"


def test_saving_a_tag_that_hides_the_cursors_file_moves_the_cursor_to_the_next_shown_tile(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    window.grid_filter.choose(NO_TAGS)

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "beach")

    assert cursor_name(stack) == "IMG_2.png"


def test_with_the_cheat_sheet_shown_over_the_grid_a_click_on_the_filter_button_still_pops_up_its_menu(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_H)
    button = stack.currentWidget().findChild(FilterButton)

    clicked = window.childAt(button.mapTo(window, button.rect().center()))  # what a click there reaches, as Qt routes it
    QTest.mouseClick(clicked, Qt.MouseButton.LeftButton)

    assert (window.cheat_sheet.isVisible(), clicked) == (True, button)
    assert popped_up_menu(stack.currentWidget()).isVisible()



def window_on_a_folder_whose_second_and_third_images_are_tagged(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    make_image(folder / "IMG_3.png", "green")
    library = Library.open(drive)
    library.enter(folder / "IMG_2.png", "beach")
    library.enter(folder / "IMG_3.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    return window, stack, folder


def test_enter_on_a_file_of_a_filtered_folder_grid_starts_a_slideshow_over_only_the_shown_files_in_grid_order(qtbot, tmp_path):
    window, stack, folder = window_on_a_folder_whose_second_and_third_images_are_tagged(qtbot, tmp_path)
    window.grid_filter.choose(WITH_TAGS)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert (window.viewer.slideshow.items, window.viewer.slideshow.current) == ([folder / "IMG_2.png", folder / "IMG_3.png"], folder / "IMG_2.png")


def test_after_the_filter_is_turned_off_again_enter_on_a_file_starts_a_slideshow_over_every_file_of_the_folder(qtbot, tmp_path):
    window, stack, folder = window_on_a_folder_whose_second_and_third_images_are_tagged(qtbot, tmp_path)
    window.grid_filter.choose(WITH_TAGS)
    window.grid_filter.choose(WITH_TAGS)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert window.viewer.slideshow.items == [folder / "IMG_1.png", folder / "IMG_2.png", folder / "IMG_3.png"]


def test_enter_on_a_file_of_a_filtered_results_grid_starts_a_slideshow_over_only_the_shown_result_files(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    make_image(folder / "IMG_3.png", "green")
    library = Library.open(drive)
    library.enter(folder / "IMG_1.png", "beach type:photo")
    library.enter(folder / "IMG_2.png", "beach")
    library.enter(folder / "IMG_3.png", "beach")
    write_config(drive, ["type:"])
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    window.grid_filter.choose(MISSING_TAGS)
    search_for(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert window.viewer.slideshow.items == [folder / "IMG_2.png", folder / "IMG_3.png"]


def test_esc_back_from_a_filtered_slideshow_puts_the_cursor_on_the_file_that_was_showing(qtbot, tmp_path):
    window, stack, folder = window_on_a_folder_whose_second_and_third_images_are_tagged(qtbot, tmp_path)
    window.grid_filter.choose(WITH_TAGS)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(window.viewer, Qt.Key.Key_Space)

    qtbot.keyClick(window.viewer, Qt.Key.Key_Escape)

    assert cursor_name(stack) == "IMG_3.png"


def test_esc_back_from_a_filtered_slideshow_on_a_file_tagged_so_it_no_longer_matches_puts_the_cursor_on_the_next_shown_tile(qtbot, tmp_path):
    window, stack, folder = window_on_a_folder_whose_second_and_third_images_are_tagged(qtbot, tmp_path)
    window.grid_filter.choose(WITH_TAGS)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    enter_in_tag_prompt(qtbot, window.viewer, "-beach")

    qtbot.keyClick(window.viewer, Qt.Key.Key_Escape)

    assert (shown_tile_names(stack.currentWidget()), cursor_name(stack)) == (["IMG_3.png"], "IMG_3.png")
