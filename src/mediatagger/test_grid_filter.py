from PySide6.QtCore import Qt

from mediatagger.grid import Grid
from mediatagger.grid_filter import WITH_TAGS, GridFilter
from mediatagger.library import Library
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


def chosen(text):
    grid_filter = GridFilter()
    grid_filter.choose(text)
    return grid_filter


def test_with_with_tags_chosen_a_folder_grid_hides_a_file_that_has_no_own_tags(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg", "city.jpg")
    library.enter(tmp_path / "beach.jpg", "sea")
    grid = Grid(tmp_path, library=library, grid_filter=chosen(WITH_TAGS))
    qtbot.addWidget(grid)

    assert "city.jpg" not in shown_tile_names(grid)


def test_with_with_tags_chosen_a_folder_grid_keeps_showing_a_file_that_has_own_tags(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg", "city.jpg")
    library.enter(tmp_path / "beach.jpg", "sea")
    grid = Grid(tmp_path, library=library, grid_filter=chosen(WITH_TAGS))
    qtbot.addWidget(grid)

    assert shown_tile_names(grid) == ["beach.jpg"]


def test_with_with_tags_chosen_a_file_whose_only_tags_are_inherited_from_its_folder_is_hidden(qtbot, tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "trip").mkdir()
    touch(tmp_path / "trip", "beach.jpg")
    library.enter(tmp_path / "trip", "holiday")
    grid = Grid(tmp_path / "trip", library=library, grid_filter=chosen(WITH_TAGS))
    qtbot.addWidget(grid)

    assert shown_tile_names(grid) == []
