from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QStyleOptionViewItem

from mediatagger.folder import folder_entries
from mediatagger.grid import FOLDER_GLYPH, IMAGE_GLYPH, TAG_BADGE, VIDEO_BADGE, VIDEO_GLYPH, Grid
from mediatagger.library import Library
from mediatagger.test_folder import touch


def tile_names(grid):
    model = grid.model()
    return [model.index(row, 0).data(Qt.ItemDataRole.DisplayRole) for row in range(model.rowCount())]


class RecordingPainter(QPainter):
    def __init__(self, device):
        super().__init__(device)
        self.texts = []

    def drawText(self, *args):
        self.texts.extend(arg for arg in args if isinstance(arg, str))
        super().drawText(*args)


def painted_texts(grid, row):
    image = QImage(200, 200, QImage.Format.Format_ARGB32)
    painter = RecordingPainter(image)
    option = QStyleOptionViewItem()
    option.rect = QRect(0, 0, 200, 200)
    grid.itemDelegate().paint(painter, option, grid.model().index(row, 0))
    painter.end()
    return painter.texts


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


def test_a_folder_tile_draws_the_folder_glyph_an_image_tile_the_image_glyph_and_a_video_tile_the_video_glyph(qtbot, tmp_path):
    (tmp_path / "day1").mkdir()
    touch(tmp_path, "clip.mp4", "photo.jpg")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)

    assert FOLDER_GLYPH in painted_texts(grid, 0)
    assert VIDEO_GLYPH in painted_texts(grid, 1)
    assert IMAGE_GLYPH in painted_texts(grid, 2)


def test_a_video_tile_shows_a_play_badge(qtbot, tmp_path):
    touch(tmp_path, "clip.mp4")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)

    assert VIDEO_BADGE in painted_texts(grid, 0)


def test_an_image_tile_shows_no_play_badge(qtbot, tmp_path):
    touch(tmp_path, "photo.jpg")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)

    assert VIDEO_BADGE not in painted_texts(grid, 0)


def test_a_tile_whose_filename_is_wider_than_the_tile_shows_it_truncated_with_an_ellipsis(qtbot, tmp_path):
    name = "a_very_long_filename_" * 6 + ".jpg"
    touch(tmp_path, name)
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)

    texts = painted_texts(grid, 0)

    assert name not in texts
    assert any(text.endswith("…") and name.startswith(text[:-1]) for text in texts)


def test_a_tile_whose_filename_fits_shows_it_whole_with_no_ellipsis(qtbot, tmp_path):
    touch(tmp_path, "cat.jpg")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)

    texts = painted_texts(grid, 0)

    assert "cat.jpg" in texts
    assert not any("…" in text for text in texts)


def test_a_tile_for_an_item_with_3_own_tags_shows_a_tag_badge_with_its_count(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg")
    library.enter(tmp_path / "beach.jpg", "beach family summer")
    grid = Grid(tmp_path, library=library)
    qtbot.addWidget(grid)

    assert f"{TAG_BADGE}3" in painted_texts(grid, 0)


def test_a_tile_for_an_untagged_item_shows_no_tag_badge(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg", "cat.jpg")
    library.enter(tmp_path / "beach.jpg", "beach family summer")
    grid = Grid(tmp_path, library=library)
    qtbot.addWidget(grid)

    assert not any(TAG_BADGE in text for text in painted_texts(grid, 1))


def test_a_grid_with_no_library_shows_no_tag_badges(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg")
    library.enter(tmp_path / "beach.jpg", "beach family summer")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)

    assert not any(TAG_BADGE in text for text in painted_texts(grid, 0))


def test_in_the_grid_right_arrow_moves_the_cursor_to_the_next_tile_and_left_arrow_back(qtbot, tmp_path):
    touch(tmp_path, "a.jpg", "b.jpg", "c.jpg")
    grid = Grid(tmp_path, at=tmp_path / "a.jpg")
    qtbot.addWidget(grid)

    qtbot.keyClick(grid, Qt.Key.Key_Right)
    assert grid.currentIndex().data(Qt.ItemDataRole.DisplayRole) == "b.jpg"

    qtbot.keyClick(grid, Qt.Key.Key_Left)
    assert grid.currentIndex().data(Qt.ItemDataRole.DisplayRole) == "a.jpg"


def test_in_the_grid_down_arrow_moves_the_cursor_one_row_down(qtbot, tmp_path):
    touch(tmp_path, *(f"{name}.jpg" for name in "abcdefghij"))
    grid = Grid(tmp_path, at=tmp_path / "a.jpg")
    qtbot.addWidget(grid)
    grid.resize(700, 700)
    grid.show()
    qtbot.waitExposed(grid)
    start = grid.visualRect(grid.currentIndex())

    qtbot.keyClick(grid, Qt.Key.Key_Down)

    below = grid.visualRect(grid.currentIndex())
    assert (below.x(), below.y() > start.y()) == (start.x(), True)


def test_in_the_grid_plus_makes_the_tiles_bigger_than_their_starting_size_of_about_200_px(qtbot, tmp_path):
    touch(tmp_path, "a.jpg", "b.jpg")
    grid = Grid(tmp_path, at=tmp_path / "a.jpg")
    qtbot.addWidget(grid)
    grid.resize(1000, 1000)
    grid.show()
    qtbot.waitExposed(grid)

    def tile_width():
        return grid.visualRect(grid.model().index(1, 0)).x() - grid.visualRect(grid.model().index(0, 0)).x()

    start = tile_width()

    qtbot.keyClick(grid, Qt.Key.Key_Plus)

    assert abs(start - 200) <= 20
    assert tile_width() > start


def test_in_the_grid_minus_makes_the_tiles_smaller_than_their_starting_size(qtbot, tmp_path):
    touch(tmp_path, "a.jpg", "b.jpg")
    grid = Grid(tmp_path, at=tmp_path / "a.jpg")
    qtbot.addWidget(grid)
    grid.resize(1000, 1000)
    grid.show()
    qtbot.waitExposed(grid)

    def tile_width():
        return grid.visualRect(grid.model().index(1, 0)).x() - grid.visualRect(grid.model().index(0, 0)).x()

    start = tile_width()

    qtbot.keyClick(grid, Qt.Key.Key_Minus)

    assert tile_width() < start
