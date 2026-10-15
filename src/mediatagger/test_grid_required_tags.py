from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QFontMetrics, QGuiApplication, QImage, QPainter
from PySide6.QtWidgets import QStyleOptionViewItem

from mediatagger.grid import MISSING_ROOTS_BADGE, TAG_BADGE, TILE_ROLE, Grid
from mediatagger.library import Library
from mediatagger.test_folder import touch
from mediatagger.test_grid import painted_texts, painted_tile

ROOTS = ("type:", "size:")


def missing_badge(grid, row):
    return next((text for text in painted_texts(grid, row) if MISSING_ROOTS_BADGE in text), None)


def test_a_grid_given_two_required_roots_marks_an_untagged_files_tile_as_missing_both(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg")
    grid = Grid(tmp_path, library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)

    assert f"{MISSING_ROOTS_BADGE}2" in painted_texts(grid, 0)


def test_a_file_whose_own_tags_start_with_every_required_root_has_no_missing_badge(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg")
    library.enter(tmp_path / "beach.jpg", "type:photo size:big")
    grid = Grid(tmp_path, library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)

    assert missing_badge(grid, 0) is None


def test_a_root_covered_by_a_tag_inherited_from_an_ancestor_folder_is_not_missing(qtbot, tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "trip" / "day1").mkdir(parents=True)
    touch(tmp_path / "trip" / "day1", "beach.jpg")
    library.enter(tmp_path / "trip", "type:photo")
    grid = Grid(tmp_path / "trip" / "day1", library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)

    assert f"{MISSING_ROOTS_BADGE}1" in painted_texts(grid, 0)


def test_a_folder_tile_even_an_untagged_one_has_no_missing_badge(qtbot, tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "trip").mkdir()
    grid = Grid(tmp_path, library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)

    assert missing_badge(grid, 0) is None


def test_a_grid_with_no_required_roots_or_no_library_has_no_missing_badge(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg")
    grids = [Grid(tmp_path, library=library), Grid(tmp_path, required_roots=ROOTS)]
    for grid in grids:
        qtbot.addWidget(grid)

    assert [missing_badge(grid, 0) for grid in grids] == [None, None]


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
    missing, tags = painter.placed[f"{MISSING_ROOTS_BADGE}2"], painter.placed[f"{TAG_BADGE}2"]

    assert (missing.right() < tags.left(), missing.top() == tags.top(), tags.right() > 160) == (True, True, True)


def test_the_missing_badge_contrasts_with_its_surroundings_over_both_a_white_and_a_black_thumbnail(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "photo.jpg")
    grid = Grid(tmp_path, library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)
    tile = grid.model().index(0, 0).data(TILE_ROLE)
    metrics = QFontMetrics(QGuiApplication.font())
    badge_area = QRect(100, 0, 100, 2 * metrics.height())  # with no tag badge, it sits in the tile's top-right corner

    for color in (Qt.GlobalColor.white, Qt.GlobalColor.black):
        thumbnail = QImage(200, 200 - metrics.height(), QImage.Format.Format_RGB32)  # fills the tile's picture area
        thumbnail.fill(color)
        tile.thumbnail = thumbnail
        image = painted_tile(grid, 0, selected=False)
        lightnesses = [image.pixelColor(x, y).lightness()
                       for y in range(badge_area.top(), badge_area.bottom() + 1)
                       for x in range(badge_area.left(), badge_area.right() + 1)]

        assert max(lightnesses) - min(lightnesses) > 128, f"missing badge unreadable over a {color.name} thumbnail"


def test_a_results_grid_marks_result_files_by_their_effective_tags_and_never_a_result_folder_or_a_missing_result(qtbot, tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "trip").mkdir()
    (tmp_path / "album").mkdir()
    touch(tmp_path / "trip", "a.jpg")
    touch(tmp_path, "b.jpg", "gone.jpg")
    library.enter(tmp_path / "trip", "type:photo")
    for path in (tmp_path / "trip" / "a.jpg", tmp_path / "b.jpg", tmp_path / "album", tmp_path / "gone.jpg"):
        library.enter(path, "beach")
    (tmp_path / "gone.jpg").unlink()
    paths = [tmp_path / "album", tmp_path / "trip" / "a.jpg", tmp_path / "b.jpg", tmp_path / "gone.jpg"]
    grid = Grid(tmp_path, library=library, paths=paths, required_roots=ROOTS)
    qtbot.addWidget(grid)

    assert [missing_badge(grid, row) for row in range(4)] == [None, f"{MISSING_ROOTS_BADGE}1", f"{MISSING_ROOTS_BADGE}2", None]


def test_after_a_first_grid_has_been_shown_opening_the_grid_of_5000_files_half_tagged_with_two_required_roots_takes_under_150_ms(qtbot, tmp_path):
    from mediatagger.test_grid import fastest_of_three

    library = Library.create(tmp_path)
    (tmp_path / "warm-up").mkdir()
    touch(tmp_path / "warm-up", "a.jpg")
    warm_up = Grid(tmp_path / "warm-up", library=library, required_roots=ROOTS)  # the first widget shown loads Qt's fonts
    qtbot.addWidget(warm_up)
    warm_up.show()
    (tmp_path / "big").mkdir()
    names = [f"IMG_{i}.jpg" for i in range(5000)]
    touch(tmp_path / "big", *names)
    library.enter(tmp_path / "big", "place:beach")
    for name in names[::2]:
        library.enter(tmp_path / "big" / name, "type:photo people:ana")

    def open_and_show():
        grid = Grid(tmp_path / "big", library=library, required_roots=ROOTS)
        grid.show()
        return grid

    elapsed, grid = fastest_of_three(qtbot, open_and_show)

    assert (elapsed < 0.150, missing_badge(grid, 0), missing_badge(grid, 1)) == (True, f"{MISSING_ROOTS_BADGE}1", f"{MISSING_ROOTS_BADGE}2")
