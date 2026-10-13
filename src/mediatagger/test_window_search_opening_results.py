from PySide6.QtCore import Qt

from mediatagger.grid import TILE_ROLE
from mediatagger.library import Library
from mediatagger.test_grid import tile_names
from mediatagger.test_viewer import make_image, shown_texts
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
from mediatagger.test_window import window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.test_window_search import drive_with_a_missing_image_tagged, search_for
from mediatagger.viewer import Viewer


def test_enter_on_a_result_file_opens_a_slideshow_at_that_file(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    make_image(folder / "IMG_2.png", "blue")
    library.enter(folder / "IMG_1.png", "beach")
    library.enter(folder / "IMG_2.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == folder / "IMG_2.png"


def test_next_in_a_slideshow_opened_from_results_goes_to_the_next_result_file(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    make_image(folder / "IMG_2.png", "blue")
    make_image(folder / "IMG_3.png", "green")
    library.enter(folder / "IMG_1.png", "beach")
    library.enter(folder / "IMG_3.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    assert stack.currentWidget().slideshow.current == folder / "IMG_3.png"


def test_a_slideshow_opened_from_results_skips_result_folders_and_missing_paths(qtbot, tmp_path):
    drive, folder = drive_with_a_missing_image_tagged(tmp_path, "beach")
    library = Library.open(drive)
    make_image(folder / "IMG_3.png", "green")
    summer = drive / "Trips" / "Summer"
    summer.mkdir(parents=True)
    for path in (summer, folder / "IMG_1.png", folder / "IMG_3.png"):
        library.enter(path, "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_I)

    [overlay] = [text for text in shown_texts(stack.currentWidget()) if "IMG_1.png" in text]
    assert "1 / 2" in overlay


def test_esc_in_a_slideshow_opened_from_results_returns_to_the_results_grid_with_the_cursor_on_the_current_file(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    make_image(folder / "IMG_2.png", "blue")
    make_image(folder / "IMG_3.png", "green")
    library.enter(folder / "IMG_1.png", "beach")
    library.enter(folder / "IMG_3.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    results = stack.currentWidget()
    qtbot.keyClick(results, Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert (shown is results, shown.currentIndex().data(TILE_ROLE).path) == (True, folder / "IMG_3.png")


def test_enter_on_a_result_folder_opens_that_folders_unfiltered_grid_with_the_cursor_on_its_first_item_and_ends_the_search(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    summer = drive / "Trips" / "Summer"
    summer.mkdir(parents=True)
    make_image(summer / "IMG_5.png", "blue")
    make_image(summer / "IMG_6.png", "green")
    Library.open(drive).enter(summer, "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    shown = stack.currentWidget()
    assert (shown.folder, tile_names(shown), shown.currentIndex().row(), window.breadcrumb.isVisible()) == (summer, ["IMG_5.png", "IMG_6.png"], 0, False)


def test_esc_in_a_slideshow_from_a_folder_opened_from_results_returns_to_that_folder_not_to_the_results(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    summer = drive / "Trips" / "Summer"
    summer.mkdir(parents=True)
    make_image(summer / "IMG_5.png", "blue")
    library.enter(summer, "beach")
    library.enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Left)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert (shown.folder, shown.currentIndex().data(TILE_ROLE).path, window.breadcrumb.isVisible()) == (summer, summer / "IMG_5.png", False)


def test_enter_on_a_missing_tile_does_nothing(qtbot, tmp_path):
    drive, folder = drive_with_a_missing_image_tagged(tmp_path, "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    results = stack.currentWidget()

    qtbot.keyClick(results, Qt.Key.Key_Return)

    shown = stack.currentWidget()
    assert (shown is results, shown.currentIndex().data(TILE_ROLE).path, window.breadcrumb.isVisible()) == (True, folder / "IMG_2.png", True)


def test_after_esc_ends_a_search_esc_in_a_slideshow_from_the_folder_returns_to_the_folder_not_to_the_results(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert tile_names(stack.currentWidget()) == ["IMG_1.png", "IMG_2.png"]
