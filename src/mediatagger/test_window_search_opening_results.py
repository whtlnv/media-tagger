from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget

from mediatagger.grid import TILE_ROLE
from mediatagger.library import Library
from mediatagger.test_grid import tile_names
from mediatagger.test_viewer import SILENT, make_image, shown_texts
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders
from mediatagger.test_window import window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.test_window_search import drive_with_a_missing_image_tagged, search_for
from mediatagger.viewer import Viewer
from mediatagger.window import Window


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


def test_opening_a_result_file_hides_the_search_label(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert (isinstance(stack.currentWidget(), Viewer), window.breadcrumb.isVisible()) == (True, False)


def test_esc_from_a_result_file_shows_the_search_label_again_with_the_same_query(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert (window.breadcrumb.isVisible(), window.breadcrumb.text()) == (True, "Search: beach")


def test_enter_on_a_search_with_no_results_does_nothing_and_keeps_the_search_label(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "mountain")
    results = stack.currentWidget()

    qtbot.keyClick(results, Qt.Key.Key_Return)

    assert (stack.currentWidget() is results, window.breadcrumb.isVisible(), window.breadcrumb.text()) == (True, True, "Search: mountain")


def test_esc_in_a_slideshow_of_a_folder_picked_from_the_results_grid_after_a_results_slideshow_shows_that_folders_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    [chosen] = make_folders(drive, "Chosen")
    make_image(chosen / "x.jpg", "green")
    window = Window(folder, player_options=SILENT, folder_picker=lambda: chosen, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_O)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert (shown.folder, tile_names(shown)) == (chosen, ["x.jpg"])


def test_esc_in_a_slideshow_of_a_folder_picked_during_a_results_slideshow_shows_that_folders_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    [chosen] = make_folders(drive, "Chosen")
    make_image(chosen / "x.jpg", "green")
    window = Window(folder, player_options=SILENT, folder_picker=lambda: chosen, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_O)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert (shown.folder, tile_names(shown)) == (chosen, ["x.jpg"])


def test_esc_in_a_slideshow_of_a_folder_dropped_during_a_results_slideshow_shows_that_folders_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    [dropped] = make_folders(drive, "Dropped")
    make_image(dropped / "x.jpg", "green")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    drag_and_drop_onto(stack.currentWidget(), dropped)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert (shown.folder, tile_names(shown)) == (dropped, ["x.jpg"])
