from PySide6.QtCore import Qt

from mediatagger.folder import folder_entries
from mediatagger.grid import Grid
from mediatagger.test_folder import touch


def tile_names(grid):
    model = grid.model()
    return [model.index(row, 0).data(Qt.ItemDataRole.DisplayRole) for row in range(model.rowCount())]


def test_the_grid_of_a_folder_shows_one_tile_per_listed_entry_subfolders_first_in_listing_order(qtbot, tmp_path):
    touch(tmp_path, "IMG_10.jpg", "clip_2.mp4", "IMG_1.jpg", "notes.txt")
    (tmp_path / "day10").mkdir()
    (tmp_path / "day2").mkdir()
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)

    assert tile_names(grid) == ["day2", "day10", "clip_2.mp4", "IMG_1.jpg", "IMG_10.jpg"]
    assert tile_names(grid) == [entry.name for entry in folder_entries(tmp_path)]


def test_the_grid_opened_on_a_folder_at_a_given_file_has_its_cursor_on_that_file(qtbot, tmp_path):
    touch(tmp_path, "a.jpg", "b.jpg", "c.jpg")
    grid = Grid(tmp_path, at=tmp_path / "b.jpg")
    qtbot.addWidget(grid)

    assert grid.currentIndex().data(Qt.ItemDataRole.DisplayRole) == "b.jpg"
