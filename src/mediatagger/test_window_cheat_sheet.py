from PySide6.QtCore import Qt
from PySide6.QtGui import qBlue, qGreen, qRed
from PySide6.QtWidgets import QStackedWidget

from mediatagger.grid import TILE_ROLE
from mediatagger.test_viewer import SILENT, make_image
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
    window.resize(800, 600)
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
