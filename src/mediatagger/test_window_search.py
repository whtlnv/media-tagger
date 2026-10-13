from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QLineEdit

from mediatagger.library import Library
from mediatagger.test_grid import tile_names
from mediatagger.test_viewer import make_image
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, drive_without_a_tag_library_holding_one_image
from mediatagger.test_window import window_showing_the_grid_with_its_cursor_on_its_first_tile


def test_pressing_slash_in_the_windows_grid_on_a_drive_with_a_library_shows_a_search_bar_above_the_grid_with_keyboard_focus(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    grid = stack.currentWidget()

    qtbot.keyClick(grid, Qt.Key.Key_Slash)

    [bar] = [line for line in window.findChildren(QLineEdit) if line.isVisible()]
    assert window.focusWidget() is bar
    assert bar.mapTo(window, QPoint(0, bar.height())).y() <= grid.mapTo(window, QPoint(0, 0)).y()


def test_pressing_slash_in_the_windows_grid_on_a_drive_without_a_library_shows_no_search_bar(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    assert [line for line in window.findChildren(QLineEdit) if line.isVisible()] == []


def test_typing_a_query_and_pressing_enter_replaces_the_grid_with_tiles_of_the_matching_items_named_by_their_own_names_in_results_order(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    for name in ("IMG_10.png", "IMG_2.png"):
        make_image(folder / name, "blue")
        library.enter(folder / name, "beach")
    summer = drive / "Trips" / "Summer"
    summer.mkdir(parents=True)
    library.enter(summer, "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    assert tile_names(stack.currentWidget()) == ["Summer", "IMG_2.png", "IMG_10.png"]
