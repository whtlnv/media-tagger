from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget

from mediatagger.test_viewer import SILENT, make_image
from mediatagger.window import Window


def pixels_outside(image, tile):
    return [image.pixel(x, y) for y in range(image.height()) for x in range(image.width()) if not tile.contains(x, y)]


def test_in_the_windows_folder_grid_pressing_h_draws_text_over_the_empty_background_where_before_it_was_plain(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    window.resize(800, 600)
    window.show()
    qtbot.waitExposed(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    grid = stack.currentWidget()
    tile = grid.visualRect(grid.model().index(0, 0))
    before = pixels_outside(grid.viewport().grab().toImage(), tile)

    qtbot.keyClick(grid, Qt.Key.Key_H)

    after = pixels_outside(grid.viewport().grab().toImage(), tile)
    assert len(set(before)) == 1
    assert len(set(after)) > 1
