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


def test_a_file_whose_own_tags_start_with_every_required_root_has_no_missing_badge(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg")
    library.enter(tmp_path / "beach.jpg", "type:photo size:big")
    grid = Grid(tmp_path, library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)

    assert not any(MISSING_BADGE in text for text in painted_texts(grid, 0))


def test_a_root_covered_by_a_tag_inherited_from_an_ancestor_folder_is_not_missing(qtbot, tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "trip" / "day1").mkdir(parents=True)
    touch(tmp_path / "trip" / "day1", "beach.jpg")
    library.enter(tmp_path / "trip", "type:photo")
    grid = Grid(tmp_path / "trip" / "day1", library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)

    assert f"{MISSING_BADGE}1" in painted_texts(grid, 0)
