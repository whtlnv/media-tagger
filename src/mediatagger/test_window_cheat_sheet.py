from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, qBlue, qGreen, qRed
from PySide6.QtWidgets import QStackedWidget

from mediatagger.cheat_sheet import GRID_KEYS, LAUNCH_KEYS, VIEWER_KEYS, CheatSheet
from mediatagger.grid import TILE_ROLE
from mediatagger.image_fit import fitted_rect
from mediatagger.library import Library
from mediatagger.test_viewer import SILENT, make_image
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, visible_tag_prompts
from mediatagger.test_window import window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.test_window_search import search_for
from mediatagger.test_window_state import state_file_path
from mediatagger.window import Window


def pixels_outside(image, tile):
    return [image.pixel(x, y) for y in range(image.height()) for x in range(image.width()) if not tile.contains(x, y)]


def is_red(pixel):
    return qRed(pixel) > 200 and qGreen(pixel) < 60 and qBlue(pixel) < 60


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


def test_in_the_windows_folder_grid_pressing_h_draws_text_over_the_empty_background_where_before_it_was_plain(qtbot, tmp_path):
    grid, tile = grid_of_one_red_image(qtbot, tmp_path)
    before = pixels_outside(grid.viewport().grab().toImage(), tile)

    qtbot.keyClick(grid, Qt.Key.Key_H)

    after = pixels_outside(grid.viewport().grab().toImage(), tile)
    assert len(set(before)) == 1
    assert len(set(after)) > 1


def test_in_the_windows_folder_grid_pressing_h_a_second_time_leaves_the_empty_background_plain_again(qtbot, tmp_path):
    grid, tile = grid_of_one_red_image(qtbot, tmp_path)
    qtbot.keyClick(grid, Qt.Key.Key_H)

    qtbot.keyClick(grid, Qt.Key.Key_H)

    assert len(set(pixels_outside(grid.viewport().grab().toImage(), tile))) == 1


def test_pressing_h_in_the_windows_folder_grid_leaves_its_tiles_pictures_as_they_were_drawn_without_the_sheet(qtbot, tmp_path):
    grid, tile = grid_of_one_red_image(qtbot, tmp_path)
    qtbot.waitUntil(lambda: grid.model().index(0, 0).data(TILE_ROLE).thumbnail is not None)
    before = grid.viewport().grab().toImage()
    picture = [(x, y) for y in range(tile.top(), tile.bottom()) for x in range(tile.left(), tile.right()) if is_red(before.pixel(x, y))]

    qtbot.keyClick(grid, Qt.Key.Key_H)

    after = grid.viewport().grab().toImage()
    assert len(picture) > 1000
    assert all(after.pixel(x, y) == before.pixel(x, y) for x, y in picture)


def viewer_of_one_red_image(qtbot, folder):
    """The window's viewer showing a 64x48 red image, fitted into a wider viewer so black lies either side of it,
    and the fitted picture's rectangle."""
    make_image(folder / "a.png", "red")
    window = Window(folder, player_options=SILENT)
    qtbot.addWidget(window)
    window.resize(1000, 600)
    window.show()
    qtbot.waitExposed(window)
    return window.viewer, fitted_rect(QSize(64, 48), window.viewer.rect())


def test_in_the_windows_viewer_pressing_h_draws_dim_text_in_the_black_around_the_picture_and_leaves_the_picture_as_it_was(qtbot, tmp_path):
    viewer, picture = viewer_of_one_red_image(qtbot, tmp_path)
    before = viewer.grab().toImage()
    assert set(pixels_outside(before, picture)) == {QColor("black").rgb()}

    qtbot.keyClick(viewer, Qt.Key.Key_H)

    after = viewer.grab().toImage()
    around = pixels_outside(after, picture)
    brightest = max(max(qRed(pixel), qGreen(pixel), qBlue(pixel)) for pixel in around)
    assert 40 <= brightest <= 128
    inside = [(x, y) for y in range(picture.top(), picture.bottom() + 1) for x in range(picture.left(), picture.right() + 1)]
    assert all(after.pixel(x, y) == before.pixel(x, y) for x, y in inside)


def sheet_on_black(size, keys):
    """What a shown cheat sheet of these keys looks like alone on black, at this size."""
    image = QImage(size, QImage.Format.Format_RGB32)
    image.fill(QColor("black"))
    painter = QPainter(image)
    CheatSheet(shown=True).paint(painter, image.rect(), keys, QColor("white"))
    painter.end()
    return image


def test_the_windows_viewer_shows_the_viewers_keys_around_the_picture_rather_than_the_grids(qtbot, tmp_path):
    viewer, picture = viewer_of_one_red_image(qtbot, tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_H)

    around = pixels_outside(viewer.grab().toImage(), picture)
    assert around == pixels_outside(sheet_on_black(viewer.size(), VIEWER_KEYS), picture)
    assert around != pixels_outside(sheet_on_black(viewer.size(), GRID_KEYS), picture)


def test_on_the_windows_empty_launch_screen_pressing_h_shows_the_launch_screens_keys(qtbot, tmp_path):
    window = Window(player_options=SILENT, home=tmp_path)
    qtbot.addWidget(window)
    window.resize(1000, 600)
    window.show()
    qtbot.waitExposed(window)
    message = window.viewer.placeholder.geometry()

    qtbot.keyClick(window.viewer, Qt.Key.Key_H)

    around = pixels_outside(window.viewer.grab().toImage(), message)
    assert around == pixels_outside(sheet_on_black(window.viewer.size(), LAUNCH_KEYS), message)


def test_with_the_sheet_shown_in_the_grid_opening_an_image_shows_it_in_the_viewer_and_esc_back_to_the_grid_still_shows_it(qtbot, tmp_path):
    grid, tile = grid_of_one_red_image(qtbot, tmp_path)
    qtbot.keyClick(grid, Qt.Key.Key_H)
    viewer = grid.window().viewer

    qtbot.keyClick(grid, Qt.Key.Key_Return)

    assert len(set(pixels_outside(viewer.grab().toImage(), fitted_rect(QSize(64, 48), viewer.rect())))) > 1
    qtbot.keyClick(viewer, Qt.Key.Key_Escape)
    grid_again = grid.window().findChild(QStackedWidget).currentWidget()
    assert grid_again is not viewer
    assert len(set(pixels_outside(grid_again.viewport().grab().toImage(), tile))) > 1


def test_a_results_grid_shows_the_cheat_sheet_when_it_is_on_and_h_there_hides_it(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_H)

    search_for(qtbot, window, stack, "beach")

    results = stack.currentWidget()
    tile = results.visualRect(results.model().index(0, 0))
    assert len(set(pixels_outside(results.viewport().grab().toImage(), tile))) > 1
    qtbot.keyClick(results, Qt.Key.Key_H)
    assert len(set(pixels_outside(results.viewport().grab().toImage(), tile))) == 1


def test_scrolling_a_grid_of_many_tiles_with_the_sheet_shown_leaves_the_sheet_where_it_was_drawn_whole(qtbot, tmp_path):
    for number in range(60):
        make_image(tmp_path / f"IMG_{number:02}.png", "red")
    window = Window(tmp_path / "IMG_00.png", player_options=SILENT)
    qtbot.addWidget(window)
    window.resize(500, 400)
    window.show()
    qtbot.waitExposed(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    grid = stack.currentWidget()
    qtbot.keyClick(grid, Qt.Key.Key_H)
    qtbot.wait(50)

    grid.verticalScrollBar().setValue(37)
    qtbot.wait(50)

    on_screen = window.screen().grabWindow(window.winId()).toImage()  # what the window's backing store holds, scrolled or not
    viewport = grid.viewport()
    at = viewport.mapTo(window, viewport.rect().topLeft())
    assert on_screen.copy(at.x(), at.y(), viewport.width(), viewport.height()) == viewport.grab().toImage()


def grid_background_shows_text(grid):
    tile = grid.visualRect(grid.model().index(0, 0))
    return len(set(pixels_outside(grid.viewport().grab().toImage(), tile))) > 1


def test_after_pressing_h_a_window_started_next_time_with_the_same_home_shows_the_sheet_from_the_start(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_H)
    window.close()

    next_window, next_stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    assert grid_background_shows_text(next_stack.currentWidget())


def test_with_the_sheet_remembered_as_shown_pressing_h_makes_a_window_started_next_time_with_the_same_home_start_without_it(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    first, first_stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(first_stack.currentWidget(), Qt.Key.Key_H)
    first.close()
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_H)
    window.close()

    next_window, next_stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)

    assert not grid_background_shows_text(next_stack.currentWidget())


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
    assert not grid_background_shows_text(stack.currentWidget())


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
    assert window.viewer.cheat_sheet.shown is False


def test_typing_h_into_the_search_bar_puts_an_h_in_the_search_and_leaves_the_sheet_as_it_was(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClick(window.search_bar, Qt.Key.Key_H)

    assert window.search_bar.text() == "h"
    assert not grid_background_shows_text(stack.currentWidget())
