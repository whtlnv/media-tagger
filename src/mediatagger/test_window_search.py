from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QLabel, QLineEdit

from mediatagger.library import Library
from mediatagger.state import remembered_folder, state_file
from mediatagger import grid as grid_module
from mediatagger.grid import TAG_BADGE, TILE_ROLE
from mediatagger.test_grid import painted_texts, tile_names
from mediatagger.test_viewer import make_image
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, drive_without_a_tag_library_holding_one_image
from mediatagger.test_window import enter_in_the_grids_tag_prompt, shown_status_bar_texts, window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.thumbnails import thumbnail_and_duration


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


def test_after_enter_runs_a_search_the_search_bar_is_hidden_and_the_results_grid_has_focus_with_its_cursor_on_the_first_result(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    for name in ("IMG_1.png", "IMG_2.png"):
        make_image(folder / name, "blue")
        library.enter(folder / name, "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    results = stack.currentWidget()
    visible_lines = [line for line in window.findChildren(QLineEdit) if line.isVisible()]
    assert (visible_lines, window.focusWidget() is results, results.currentIndex().row()) == ([], True, 0)


def test_after_enter_runs_a_search_a_breadcrumb_line_above_the_results_grid_reads_search_and_the_query(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    results = stack.currentWidget()
    [crumb] = [label for label in window.findChildren(QLabel) if label.isVisible() and label.text() == "Search: beach"]
    assert crumb.mapTo(window, QPoint(0, crumb.height())).y() <= results.mapTo(window, QPoint(0, 0)).y()


def test_a_search_with_no_matches_shows_the_search_breadcrumb_over_an_empty_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "mountain")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    results = stack.currentWidget()
    [crumb] = [label for label in window.findChildren(QLabel) if label.isVisible() and label.text() == "Search: mountain"]
    assert crumb.mapTo(window, QPoint(0, crumb.height())).y() <= results.mapTo(window, QPoint(0, 0)).y()
    assert tile_names(results) == []


def test_a_search_run_from_a_subfolder_finds_tagged_items_elsewhere_on_the_same_drive(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    subfolder = folder / "2024"
    subfolder.mkdir()
    make_image(subfolder / "IMG_3.png", "red")
    elsewhere = drive / "Trips"
    elsewhere.mkdir()
    make_image(elsewhere / "IMG_5.png", "blue")
    Library.open(drive).enter(elsewhere / "IMG_5.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, subfolder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    assert tile_names(stack.currentWidget()) == ["IMG_5.png"]


def test_enter_on_a_blank_query_closes_the_search_bar_and_returns_focus_to_the_unchanged_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    grid = stack.currentWidget()
    names = tile_names(grid)
    qtbot.keyClick(grid, Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "   ")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    visible_lines = [line for line in window.findChildren(QLineEdit) if line.isVisible()]
    assert (visible_lines, stack.currentWidget() is grid, window.focusWidget() is grid, tile_names(grid)) == ([], True, True, names)


def test_esc_while_typing_in_the_search_bar_closes_it_and_returns_focus_to_the_unchanged_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    grid = stack.currentWidget()
    names = tile_names(grid)
    qtbot.keyClick(grid, Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "bea")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Escape)

    visible_lines = [line for line in window.findChildren(QLineEdit) if line.isVisible()]
    assert (window.isVisible(), visible_lines, stack.currentWidget() is grid, window.focusWidget() is grid, tile_names(grid)) == (True, [], True, True, names)


def test_esc_in_the_results_grid_shows_the_folder_searched_from_with_the_cursor_where_it_was(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    for name in ("IMG_2.png", "IMG_3.png"):
        make_image(folder / name, "blue")
    library.enter(folder / "IMG_3.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    names = tile_names(stack.currentWidget())
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert (tile_names(shown), shown.currentIndex().data(Qt.ItemDataRole.DisplayRole), window.focusWidget() is shown) == (names, "IMG_2.png", True)


def test_backspace_in_the_results_grid_leaves_the_results_shown(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)
    results = stack.currentWidget()

    qtbot.keyClick(results, Qt.Key.Key_Backspace)

    assert (stack.currentWidget() is results, tile_names(results), window.breadcrumb.isVisible(), window.focusWidget() is results) == (True, ["IMG_1.png"], True, True)


def test_slash_in_the_results_grid_opens_the_search_bar_and_a_new_query_replaces_the_results(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    make_image(folder / "IMG_2.png", "blue")
    library.enter(folder / "IMG_1.png", "beach")
    library.enter(folder / "IMG_2.png", "pool")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    bar_opened_with_focus = window.search_bar.isVisible() and window.focusWidget() is window.search_bar
    window.search_bar.clear()
    qtbot.keyClicks(window.search_bar, "pool")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    assert (bar_opened_with_focus, tile_names(stack.currentWidget()), window.breadcrumb.text()) == (True, ["IMG_2.png"], "Search: pool")


def test_showing_search_results_does_not_change_the_remembered_last_folder(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    assert remembered_folder(state_file(tmp_path)) == folder


def test_a_result_tiles_badge_counts_the_items_own_tags_not_those_inherited_from_its_folders(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    library.enter(folder, "beach summer")
    library.enter(folder / "IMG_1.png", "family")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "family")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    assert [text for text in painted_texts(stack.currentWidget(), 0) if TAG_BADGE in text] == [f"{TAG_BADGE}1"]


def test_a_result_files_tile_shows_the_thumbnail_already_cached_on_its_drive_without_generating_it_again(qtbot, tmp_path, monkeypatch):
    generated = []

    def generate(path):
        generated.append(path)
        return thumbnail_and_duration(path)

    monkeypatch.setattr(grid_module, "thumbnail_and_duration", generate)
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    folder_tile = stack.currentWidget().model().index(0, 0).data(TILE_ROLE)
    qtbot.waitUntil(lambda: folder_tile.thumbnail is not None)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)
    result_tile = stack.currentWidget().model().index(0, 0).data(TILE_ROLE)
    qtbot.waitUntil(lambda: result_tile.thumbnail is not None)

    assert generated == [folder / "IMG_1.png"]


def test_moving_the_cursor_onto_a_result_shows_that_results_tags_in_the_status_bar(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    make_image(folder / "IMG_2.png", "blue")
    library.enter(folder / "IMG_1.png", "beach")
    library.enter(folder / "IMG_2.png", "beach family")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    assert "beach family" in shown_status_bar_texts(window)


def test_entering_family_in_the_tag_prompt_on_a_result_adds_it_to_that_item_and_its_badge_updates_in_place(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    qtbot.keyClicks(window.search_bar, "beach")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)
    results = stack.currentWidget()

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "family")

    assert Library.open(drive).tags(folder / "IMG_1.png") == ["beach", "family"]
    assert stack.currentWidget() is results
    assert f"{TAG_BADGE}2" in painted_texts(results, results.currentIndex().row())
