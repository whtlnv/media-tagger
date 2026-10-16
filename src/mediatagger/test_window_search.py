from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PySide6.QtWidgets import QLabel, QLineEdit, QStackedWidget

from mediatagger.library import Library
from mediatagger.state import remembered_folder, state_file
from mediatagger import grid as grid_module
from mediatagger.grid import FOLDER_GLYPH, IMAGE_GLYPH, MISSING_GLYPH, TAG_BADGE, TILE_ROLE, VIDEO_GLYPH
from mediatagger.grid import Grid
from mediatagger.search import search
from mediatagger.test_grid import fastest_of_three, painted_texts, tile_names
from mediatagger.test_viewer import SILENT, make_image
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, drive_without_a_tag_library_holding_one_image, visible_tag_prompts
from mediatagger.test_window import enter_in_the_grids_tag_prompt, shown_status_bar_texts, shown_texts_outside_the_status_bar, window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.test_viewer_open import make_folders
from mediatagger.thumbnails import thumbnail_and_duration
from mediatagger.viewer import Viewer
from mediatagger.test_window_rename import rename_prompt_after_typing
from mediatagger.window import Window


def search_for(qtbot, window, stack, query):
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    qtbot.keyClicks(window.search_bar, query)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)


def drive_with_a_missing_image_tagged(tmp_path, tags):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", tags)
    (folder / "IMG_2.png").unlink()
    return drive, folder


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

    search_for(qtbot, window, stack, "beach")

    assert tile_names(stack.currentWidget()) == ["Summer", "IMG_2.png", "IMG_10.png"]


def test_after_enter_runs_a_search_the_search_bar_is_hidden_and_the_results_grid_has_focus_with_its_cursor_on_the_first_result(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    for name in ("IMG_1.png", "IMG_2.png"):
        make_image(folder / name, "blue")
        library.enter(folder / name, "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "beach")

    results = stack.currentWidget()
    visible_lines = [line for line in window.findChildren(QLineEdit) if line.isVisible()]
    assert (visible_lines, window.focusWidget() is results, results.currentIndex().row()) == ([], True, 0)


def test_after_enter_runs_a_search_a_breadcrumb_line_above_the_results_grid_reads_search_and_the_query(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "beach")

    results = stack.currentWidget()
    [crumb] = [label for label in window.findChildren(QLabel) if label.isVisible() and label.text() == "Search: beach"]
    assert crumb.mapTo(window, QPoint(0, crumb.height())).y() <= results.mapTo(window, QPoint(0, 0)).y()


def test_a_search_with_no_matches_shows_the_search_breadcrumb_over_an_empty_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "mountain")

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

    search_for(qtbot, window, stack, "beach")

    assert tile_names(stack.currentWidget()) == ["IMG_5.png"]


def test_enter_on_a_blank_query_closes_the_search_bar_and_returns_focus_to_the_unchanged_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    grid = stack.currentWidget()
    names = tile_names(grid)

    search_for(qtbot, window, stack, "   ")

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
    search_for(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert (tile_names(shown), shown.currentIndex().data(Qt.ItemDataRole.DisplayRole), window.focusWidget() is shown) == (names, "IMG_2.png", True)


def test_backspace_in_the_results_grid_leaves_the_results_shown(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
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
    search_for(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    bar_opened_with_focus = window.search_bar.isVisible() and window.focusWidget() is window.search_bar
    window.search_bar.clear()
    qtbot.keyClicks(window.search_bar, "pool")
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Return)

    assert (bar_opened_with_focus, tile_names(stack.currentWidget()), window.breadcrumb.text()) == (True, ["IMG_2.png"], "Search: pool")


def test_pressing_o_in_the_results_grid_opens_the_folder_picker_and_choosing_a_folder_shows_its_slideshow_from_its_first_item(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    [chosen] = make_folders(drive, "Chosen")
    make_image(chosen / "y.jpg", "blue")
    make_image(chosen / "x.jpg", "green")
    window = Window(folder, player_options=SILENT, folder_picker=lambda: chosen, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    search_for(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_O)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == chosen / "x.jpg"


def test_showing_search_results_does_not_change_the_remembered_last_folder(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "beach")

    assert remembered_folder(state_file(tmp_path)) == folder


def test_a_result_tiles_badge_counts_the_items_own_tags_not_those_inherited_from_its_folders(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    library.enter(folder, "beach summer")
    library.enter(folder / "IMG_1.png", "family")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "family")

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

    search_for(qtbot, window, stack, "beach")
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
    search_for(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    assert "beach family" in shown_status_bar_texts(window)


def test_entering_family_in_the_tag_prompt_on_a_result_adds_it_to_that_item_and_its_badge_updates_in_place(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    results = stack.currentWidget()

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "family")

    assert Library.open(drive).tags(folder / "IMG_1.png") == ["beach", "family"]
    assert stack.currentWidget() is results
    assert f"{TAG_BADGE}2" in painted_texts(results, results.currentIndex().row())


def test_pressing_n_in_the_results_grid_opens_one_empty_prompt_labelled_rename_tag_styled_like_the_tag_prompt(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_N)

    [prompt] = visible_tag_prompts(window)
    assert prompt.text() == ""
    assert prompt.styleSheet() == window.tag_prompt.input.styleSheet()
    assert "Rename tag:" in shown_texts_outside_the_status_bar(window)


def test_after_enter_on_beach_family_in_the_rename_prompt_over_search_results_esc_returns_to_a_folder_grid_whose_tile_tagged_beach_family_shows_a_tag_badge_with_count_1(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    folder_grid = stack.currentWidget()
    search_for(qtbot, window, stack, "beach")
    prompt = rename_prompt_after_typing(qtbot, window, stack.currentWidget(), "beach family")
    qtbot.keyClick(prompt, Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert stack.currentWidget() is folder_grid
    assert f"{TAG_BADGE}1" in painted_texts(folder_grid, folder_grid.currentIndex().row())


def test_typing_n_into_the_search_bar_types_an_n_and_opens_no_rename_prompt(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClicks(window.search_bar, "n")

    assert window.search_bar.text() == "n"
    assert "Rename tag:" not in shown_texts_outside_the_status_bar(window)


def test_a_result_whose_path_no_longer_exists_is_drawn_as_a_missing_tile_with_a_distinct_glyph_and_its_name(qtbot, tmp_path):
    drive, folder = drive_with_a_missing_image_tagged(tmp_path, "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "beach")

    texts = painted_texts(stack.currentWidget(), 0)
    assert (MISSING_GLYPH in texts, "IMG_2.png" in texts, MISSING_GLYPH not in (IMAGE_GLYPH, FOLDER_GLYPH, VIDEO_GLYPH)) == (True, True, True)


def test_a_result_whose_path_exists_is_not_drawn_as_missing(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "beach")

    texts = painted_texts(stack.currentWidget(), 0)
    assert (MISSING_GLYPH in texts, "IMG_1.png" in texts) == (False, True)


def test_no_thumbnail_is_requested_for_a_missing_tile(qtbot, tmp_path, monkeypatch):
    asked = []

    class AskedThumbnails(grid_module.FolderThumbnails):
        def __init__(self, paths, *args, **kwargs):
            asked.extend(paths)
            super().__init__(paths, *args, **kwargs)

        def request(self, path):
            asked.append(path)
            super().request(path)

    monkeypatch.setattr(grid_module, "FolderThumbnails", AskedThumbnails)
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    library.enter(folder / "IMG_1.png", "beach")
    make_image(folder / "IMG_0.png", "blue")
    library.enter(folder / "IMG_0.png", "beach")
    (folder / "IMG_0.png").unlink()
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "beach")
    existing_tile = stack.currentWidget().model().index(1, 0).data(TILE_ROLE)
    qtbot.waitUntil(lambda: existing_tile.thumbnail is not None)

    assert folder / "IMG_0.png" not in asked


def test_entering_minus_family_in_the_tag_prompt_on_a_missing_tile_removes_that_tag_from_the_item(qtbot, tmp_path):
    drive, folder = drive_with_a_missing_image_tagged(tmp_path, "beach family")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "-family")

    assert Library.open(drive).tags(folder / "IMG_2.png") == ["beach"]


def test_removing_a_missing_tiles_last_tag_leaves_the_tile_shown_in_the_current_results(qtbot, tmp_path):
    drive, folder = drive_with_a_missing_image_tagged(tmp_path, "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    results = stack.currentWidget()

    enter_in_the_grids_tag_prompt(qtbot, window, stack, "-beach")

    assert Library.open(drive).tags(folder / "IMG_2.png") == []
    assert stack.currentWidget() is results
    assert tile_names(results) == ["IMG_2.png"]
    assert MISSING_GLYPH in painted_texts(results, 0)


def test_esc_in_the_results_grid_clears_the_search_breadcrumb(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert [label for label in window.findChildren(QLabel) if label.isVisible() and label.text().startswith("Search:")] == []


def test_esc_after_searching_again_from_the_results_returns_to_the_folder_searched_from_first(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    folder_grid = stack.currentWidget()
    search_for(qtbot, window, stack, "beach")
    search_for(qtbot, window, stack, "family")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert stack.currentWidget() is folder_grid


def test_searching_again_after_esc_ended_a_search_and_its_results_were_deleted_shows_new_results(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    search_for(qtbot, window, stack, "beach")

    assert (tile_names(stack.currentWidget()), window.breadcrumb.text()) == (["IMG_1.png"], "Search: beach")


def test_the_results_grid_of_a_search_matching_5000_tagged_files_opens_in_under_150_ms(qtbot, tmp_path):
    library = Library.create(tmp_path)
    for album in range(50):
        folder = tmp_path / f"album-{album}"
        folder.mkdir()
        for number in range(100):
            (folder / f"IMG_{number}.jpg").touch()
            library.enter(folder / f"IMG_{number}.jpg", "beach")
    paths = search(library, "beach")

    fastest, grid = fastest_of_three(qtbot, lambda: Grid(tmp_path, library=library, paths=paths))

    assert (fastest < 0.150, grid.model().rowCount()) == (True, 5000)


def test_a_result_video_is_drawn_as_a_video_until_its_thumbnail_arrives(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    (folder / "clip.mp4").write_bytes(b"not really a video")
    Library.open(drive).enter(folder / "clip.mp4", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "beach")

    assert VIDEO_GLYPH in painted_texts(stack.currentWidget(), 0)


def test_while_the_results_thumbnails_generate_the_status_bar_counts_them(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    trips = drive / "Trips"  # outside the folder shown, so their thumbnails aren't generated before the search
    trips.mkdir()
    for name in ("IMG_2.png", "IMG_3.png"):
        make_image(trips / name, "blue")
        library.enter(trips / name, "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    seen = []
    original = window.status_bar.show_background
    window.status_bar.show_background = lambda text, finished=False: (seen.append(text), original(text, finished))

    search_for(qtbot, window, stack, "beach")

    qtbot.waitUntil(lambda: any(text.startswith("⟳ Generating thumbnails") and text.endswith("/ 2") for text in seen))


def test_the_results_grid_of_a_search_in_a_schema_version_1_library_on_a_read_only_drive_is_empty(qtbot, tmp_path):
    from mediatagger.test_library import _create_schema_version_1_library, _read_only_drive

    _create_schema_version_1_library(tmp_path, "read-only-drive")
    with _read_only_drive(tmp_path):
        library = Library.open(tmp_path)
        grid = Grid(tmp_path, library=library, paths=search(library, "beach"))
        qtbot.addWidget(grid)

    assert grid.model().rowCount() == 0


def test_the_breadcrumb_shows_the_query_literally_even_when_it_looks_like_markup(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "<b>nothing</b>")

    assert window.breadcrumb.textFormat() == Qt.TextFormat.PlainText


def test_a_search_with_no_results_shows_no_item_tags_in_the_status_bar(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "pool")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "pool")

    search_for(qtbot, window, stack, "nothing")

    assert "pool" not in shown_status_bar_texts(window)


def test_the_breadcrumb_is_drawn_in_the_status_bars_font_size(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    search_for(qtbot, window, stack, "beach")

    for label in (window.breadcrumb, window.status_bar.tags_status):
        label.ensurePolished()
    assert window.breadcrumb.font().pixelSize() == window.status_bar.tags_status.font().pixelSize()
