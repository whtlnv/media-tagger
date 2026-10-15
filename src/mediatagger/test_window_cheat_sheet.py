from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, qGreen, qRed
from PySide6.QtWidgets import QStackedWidget

from mediatagger.cheat_sheet import GRID_KEYS, LAUNCH_KEYS, VIEWER_KEYS, draw_sheet
from mediatagger.grid import TILE_ROLE
from mediatagger.library import Library
from mediatagger.test_viewer import SILENT, make_image
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, visible_tag_prompts
from mediatagger.test_window import window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.test_window_search import search_for
from mediatagger.test_window_state import state_file_path
from mediatagger.window import Window


def sheet_is_shown(window):
    return window.cheat_sheet.isVisible()


def grid_of_one_red_image(qtbot, folder):
    """The window's folder grid of one red image, reached from its viewer, and the tile's rectangle."""
    make_image(folder / "a.jpg", "red")
    window = Window(folder, player_options=SILENT)
    qtbot.addWidget(window)
    window.resize(1000, 600)
    window.show()
    qtbot.waitExposed(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    grid = stack.currentWidget()
    return grid, grid.visualRect(grid.model().index(0, 0))


def middle_of(image):
    """The window's picture between a band along its top and the status bar along its bottom, which change on their own."""
    return image.copy(0, 60, image.width(), image.height() - 140)


def with_the_panel(image, keys):
    """The window's picture with the cheat sheet panel of these keys drawn over it."""
    expected = image.copy()
    painter = QPainter(expected)
    draw_sheet(painter, expected.rect(), keys)
    painter.end()
    return expected


def test_in_the_windows_grid_pressing_h_draws_a_panel_of_the_grids_keys_over_the_middle_of_the_window_on_top_of_the_tiles(qtbot, tmp_path):
    grid, _ = grid_of_one_red_image(qtbot, tmp_path)
    qtbot.waitUntil(lambda: grid.model().index(0, 0).data(TILE_ROLE).thumbnail is not None)
    window = grid.window()
    before = window.grab().toImage()

    qtbot.keyClick(grid, Qt.Key.Key_H)

    after = middle_of(window.grab().toImage())
    assert after == middle_of(with_the_panel(before, GRID_KEYS))
    assert after != middle_of(with_the_panel(before, VIEWER_KEYS))


def test_a_results_grid_shows_the_cheat_sheet_when_it_is_on_and_h_there_hides_it(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_H)

    search_for(qtbot, window, stack, "beach")

    assert sheet_is_shown(window)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_H)
    assert not sheet_is_shown(window)


def test_after_pressing_h_a_window_started_next_time_with_the_same_home_shows_the_sheet_from_the_start(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_H)
    window.close()

    next_window, _ = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    assert sheet_is_shown(next_window)


def test_with_the_sheet_remembered_as_shown_pressing_h_makes_a_window_started_next_time_with_the_same_home_start_without_it(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    first, first_stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(first_stack.currentWidget(), Qt.Key.Key_H)
    first.close()
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_H)
    window.close()

    next_window, _ = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    assert not sheet_is_shown(next_window)


def test_toggling_the_sheet_while_the_state_file_would_lie_on_the_drive_being_viewed_writes_no_state_file(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(drive / "config"))
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_H)

    assert not state_file_path().exists()


def test_typing_h_into_the_grids_tag_prompt_puts_an_h_in_the_prompt_and_leaves_the_sheet_as_it_was(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_T)
    [prompt] = visible_tag_prompts(window)

    qtbot.keyClick(prompt, Qt.Key.Key_H)

    assert prompt.text() == "h"
    assert not sheet_is_shown(window)


def test_typing_h_into_the_viewers_tag_prompt_puts_an_h_in_the_prompt_and_leaves_the_sheet_as_it_was(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    window.resize(1000, 600)
    window.show()
    qtbot.waitExposed(window)
    qtbot.keyClick(window.viewer, Qt.Key.Key_T)
    [prompt] = visible_tag_prompts(window)

    qtbot.keyClick(prompt, Qt.Key.Key_H)

    assert prompt.text() == "h"
    assert not sheet_is_shown(window)


def test_typing_h_into_the_search_bar_puts_an_h_in_the_search_and_leaves_the_sheet_as_it_was(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClick(window.search_bar, Qt.Key.Key_H)

    assert window.search_bar.text() == "h"
    assert not sheet_is_shown(window)



def test_the_tiles_stay_visible_through_the_panel_a_red_tile_under_it_still_shows_red_darkened(qtbot, tmp_path):
    for number in range(1, 30):
        make_image(tmp_path / f"IMG_{number:02}.png", "red")
    grid, _ = grid_of_one_red_image(qtbot, tmp_path)
    window = grid.window()
    centre = window.rect().center()
    qtbot.waitUntil(lambda: qRed(window.grab().toImage().pixel(centre)) > 200)  # the middle tile's thumbnail has arrived
    before = window.grab().toImage()
    red = [(x, y) for y in range(centre.y() - 20, centre.y() + 20) for x in range(centre.x() - 50, centre.x() + 50)
        if qRed(before.pixel(x, y)) > 200 and qGreen(before.pixel(x, y)) < 60]
    assert len(red) > 1000

    qtbot.keyClick(grid, Qt.Key.Key_H)

    after = window.grab().toImage()
    darkened_red = [(x, y) for x, y in red if 40 < qRed(after.pixel(x, y)) < qRed(before.pixel(x, y)) and qGreen(after.pixel(x, y)) < 40]
    assert len(darkened_red) > len(red) / 2


def test_in_the_windows_grid_pressing_h_a_second_time_removes_the_panel_leaving_the_window_as_it_was(qtbot, tmp_path):
    grid, _ = grid_of_one_red_image(qtbot, tmp_path)
    qtbot.waitUntil(lambda: grid.model().index(0, 0).data(TILE_ROLE).thumbnail is not None)
    window = grid.window()
    before = middle_of(window.grab().toImage())
    qtbot.keyClick(grid, Qt.Key.Key_H)

    qtbot.keyClick(grid, Qt.Key.Key_H)

    assert middle_of(window.grab().toImage()) == before


def window_on(qtbot, path=None, **options):
    window = Window(path, player_options=SILENT, **options)
    qtbot.addWidget(window)
    window.resize(1000, 600)
    window.show()
    qtbot.waitExposed(window)
    return window


def test_in_the_windows_viewer_showing_an_image_pressing_h_draws_a_panel_of_the_viewers_keys_over_the_middle_on_top_of_the_picture(qtbot, tmp_path):
    window = window_on(qtbot, make_image(tmp_path / "a.png", "red"))
    before = window.grab().toImage()

    qtbot.keyClick(window.viewer, Qt.Key.Key_H)

    after = middle_of(window.grab().toImage())
    assert after == middle_of(with_the_panel(before, VIEWER_KEYS))
    assert after != middle_of(with_the_panel(before, GRID_KEYS))


def test_on_the_windows_empty_launch_screen_pressing_h_draws_a_panel_of_the_launch_screens_keys(qtbot, tmp_path):
    window = window_on(qtbot, home=tmp_path)
    before = window.grab().toImage()

    qtbot.keyClick(window.viewer, Qt.Key.Key_H)

    after = middle_of(window.grab().toImage())
    assert after == middle_of(with_the_panel(before, LAUNCH_KEYS))
    assert after != middle_of(with_the_panel(before, VIEWER_KEYS))


def panel_lists(window, keys):
    """Whether the window's shown cheat sheet, drawn alone on a plain backdrop, is the panel of these keys."""
    drawn = window.cheat_sheet.grab().toImage()
    expected = QImage(drawn.size(), drawn.format())
    expected.fill(drawn.pixel(0, 0))  # the backdrop, in a corner the panel never reaches
    painter = QPainter(expected)
    draw_sheet(painter, expected.rect(), keys)
    painter.end()
    return drawn == expected


def test_with_the_panel_shown_in_the_grid_opening_an_image_shows_the_viewers_keys_and_esc_back_to_the_grid_shows_the_grids_keys(qtbot, tmp_path):
    grid, _ = grid_of_one_red_image(qtbot, tmp_path)
    window = grid.window()
    qtbot.keyClick(grid, Qt.Key.Key_H)
    assert panel_lists(window, GRID_KEYS)

    qtbot.keyClick(grid, Qt.Key.Key_Return)

    assert panel_lists(window, VIEWER_KEYS)
    qtbot.keyClick(window.viewer, Qt.Key.Key_Escape)
    assert panel_lists(window, GRID_KEYS)
