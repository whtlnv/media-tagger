from PySide6.QtCore import Qt

from mediatagger.grid import Grid
from mediatagger.grid_filter import GridFilter
from mediatagger.test_folder import touch


def shown_tile_names(grid):
    model = grid.model()
    return [model.index(row, 0).data(Qt.ItemDataRole.DisplayRole)
            for row in range(model.rowCount()) if not grid.isRowHidden(row)]


def test_in_a_folder_grid_sharing_the_windows_filter_with_no_filter_chosen_every_file_tile_shows(qtbot, tmp_path):
    touch(tmp_path, "a.jpg", "b.mp4", "c.jpg")
    grid = Grid(tmp_path, grid_filter=GridFilter())
    qtbot.addWidget(grid)

    assert shown_tile_names(grid) == ["a.jpg", "b.mp4", "c.jpg"]
