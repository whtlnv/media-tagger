from PySide6.QtCore import QRect
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QStyleOptionViewItem

from mediatagger.grid import MISSING_BADGE, TAG_BADGE, Grid
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


def test_a_folder_tile_even_an_untagged_one_has_no_missing_badge(qtbot, tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "trip").mkdir()
    grid = Grid(tmp_path, library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)

    assert not any(MISSING_BADGE in text for text in painted_texts(grid, 0))


def test_a_grid_with_no_required_roots_or_no_library_has_no_missing_badge(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg")
    grids = [Grid(tmp_path, library=library), Grid(tmp_path, required_roots=ROOTS)]
    for grid in grids:
        qtbot.addWidget(grid)

    assert [any(MISSING_BADGE in text for text in painted_texts(grid, 0)) for grid in grids] == [False, False]


class PlacementRecordingPainter(QPainter):
    """Records where each text lands: the rectangle it takes up inside the one it was drawn into."""

    def __init__(self, device):
        super().__init__(device)
        self.placed = {}

    def drawText(self, *args):
        if isinstance(args[0], QRect) and len(args) == 3:
            self.placed[args[2]] = self.boundingRect(*args)
        super().drawText(*args)


def test_on_a_tile_with_both_badges_the_missing_badge_sits_left_of_the_tag_badge_in_the_top_right_corner(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg")
    library.enter(tmp_path / "beach.jpg", "beach family")
    grid = Grid(tmp_path, library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)
    image = QImage(200, 200, QImage.Format.Format_ARGB32)
    painter = PlacementRecordingPainter(image)
    option = QStyleOptionViewItem()
    option.rect = QRect(0, 0, 200, 200)
    grid.itemDelegate().paint(painter, option, grid.model().index(0, 0))
    painter.end()
    missing, tags = painter.placed[f"{MISSING_BADGE}2"], painter.placed[f"{TAG_BADGE}2"]

    assert (missing.right() < tags.left(), missing.top() == tags.top(), tags.right() > 160) == (True, True, True)
