from mediatagger.grid import MISSING_BADGE, Grid
from mediatagger.library import Library
from mediatagger.test_folder import touch
from mediatagger.test_grid import painted_texts

ROOTS = ("type:", "size:")


def test_a_grid_given_two_required_roots_marks_an_untagged_files_tile_as_missing_both(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg")
    grid = Grid(tmp_path, library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)

    assert f"{MISSING_BADGE}2" in painted_texts(grid, 0)
