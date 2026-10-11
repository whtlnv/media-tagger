import base64
import shutil
import time

import pytest
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QFontMetrics, QGuiApplication, QImage, QPainter
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem

from mediatagger.folder import folder_entries
from mediatagger.grid import FOLDER_GLYPH, IMAGE_GLYPH, TAG_BADGE, TILE_ROLE, VIDEO_BADGE, VIDEO_GLYPH, Grid
from mediatagger.library import Library
from mediatagger.test_folder import touch
from mediatagger.test_video import make_clip
from mediatagger.thumbnails import format_duration


def tile_names(grid):
    model = grid.model()
    return [model.index(row, 0).data(Qt.ItemDataRole.DisplayRole) for row in range(model.rowCount())]


def tile_width(grid):
    return grid.visualRect(grid.model().index(1, 0)).x() - grid.visualRect(grid.model().index(0, 0)).x()


def shown_two_tile_grid(qtbot, tmp_path, width):
    touch(tmp_path, "a.jpg", "b.jpg")
    grid = Grid(tmp_path, at=tmp_path / "a.jpg")
    qtbot.addWidget(grid)
    grid.resize(width, 1000)
    grid.show()
    qtbot.waitExposed(grid)
    return grid


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
    grid = shown_two_tile_grid(qtbot, tmp_path, width=1000)

    start = tile_width(grid)

    qtbot.keyClick(grid, Qt.Key.Key_Plus)

    assert abs(start - 200) <= 20
    assert tile_width(grid) > start


def test_in_the_grid_minus_makes_the_tiles_smaller_than_their_starting_size(qtbot, tmp_path):
    grid = shown_two_tile_grid(qtbot, tmp_path, width=1000)

    start = tile_width(grid)

    qtbot.keyClick(grid, Qt.Key.Key_Minus)

    assert tile_width(grid) < start


def test_in_the_grid_pressing_plus_repeatedly_stops_growing_the_tiles_at_about_400_px(qtbot, tmp_path):
    grid = shown_two_tile_grid(qtbot, tmp_path, width=2000)

    for _ in range(10):
        qtbot.keyClick(grid, Qt.Key.Key_Plus)

    assert abs(tile_width(grid) - 400) <= 20


def test_in_the_grid_pressing_minus_repeatedly_stops_shrinking_the_tiles_at_about_100_px(qtbot, tmp_path):
    grid = shown_two_tile_grid(qtbot, tmp_path, width=1000)

    for _ in range(10):
        qtbot.keyClick(grid, Qt.Key.Key_Minus)

    assert abs(tile_width(grid) - 100) <= 20


def test_repainting_the_grid_after_its_files_are_deleted_from_disk_still_paints_their_tiles_without_reading_them(qtbot, tmp_path):
    (tmp_path / "day1").mkdir()
    touch(tmp_path, "clip.mp4", "photo.jpg")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)

    (tmp_path / "day1").rmdir()
    (tmp_path / "clip.mp4").unlink()
    (tmp_path / "photo.jpg").unlink()

    assert FOLDER_GLYPH in painted_texts(grid, 0)
    assert VIDEO_GLYPH in painted_texts(grid, 1)
    assert IMAGE_GLYPH in painted_texts(grid, 2)


def test_after_a_first_grid_has_been_shown_opening_and_showing_the_grid_of_a_folder_of_5000_files_takes_under_150_ms(qtbot, tmp_path):
    (tmp_path / "warm-up").mkdir()
    touch(tmp_path / "warm-up", "a.jpg")
    warm_up = Grid(tmp_path / "warm-up")  # the first widget shown loads Qt's fonts, a one-off cost
    qtbot.addWidget(warm_up)
    warm_up.show()
    (tmp_path / "big").mkdir()
    touch(tmp_path / "big", *[f"IMG_{i}.jpg" for i in range(5000)])

    def open_and_show():
        grid = Grid(tmp_path / "big")
        grid.show()
        return grid

    elapsed, grid = fastest_of_three(qtbot, open_and_show)

    assert (elapsed < 0.150, grid.model().rowCount()) == (True, 5000)


def test_opening_the_grid_of_a_folder_of_5000_images_with_an_empty_cache_and_starting_its_thumbnails_takes_under_150_ms(qtbot, tmp_path):
    from PySide6.QtWidgets import QApplication

    from mediatagger.test_viewer import make_image
    from mediatagger.thumbnail_cache import ThumbnailCache

    (tmp_path / "warm-up").mkdir()
    make_image(tmp_path / "warm-up" / "a.jpg", "blue")
    warm_up = Grid(tmp_path / "warm-up")  # loads Qt's fonts and image plugins, and starts the first workers: one-off costs
    qtbot.addWidget(warm_up)
    warm_up.show()
    warm_up_tile = warm_up.model().index(0, 0).data(TILE_ROLE)
    qtbot.waitUntil(lambda: warm_up_tile.thumbnail is not None)
    (tmp_path / "big").mkdir()
    image = make_image(tmp_path / "image.jpg", "red", 1600, 1200)
    for number in range(5000):
        shutil.copyfile(image, tmp_path / "big" / f"IMG_{number}.jpg")
    def open_and_start_generating():
        grid = Grid(tmp_path / "big", thumbnail_cache=ThumbnailCache(":memory:"))  # empty every time
        grid.show()
        QApplication.processEvents()  # the first turn of the event loop, where the grid starts generating its thumbnails
        return grid

    elapsed, grid = fastest_of_three(qtbot, open_and_start_generating)

    assert (elapsed < 0.150, grid.model().rowCount()) == (True, 5000)


def fastest_of_three(qtbot, open_grid):
    """The quickest of three openings: a single one can be held up by whatever else the machine is doing at that moment.
    Each grid's thumbnail workers are stopped before the next opening, so none slows another down."""
    timings = []
    for _ in range(3):
        started = time.perf_counter()
        grid = open_grid()
        timings.append(time.perf_counter() - started)
        qtbot.addWidget(grid)
        grid.stop_generating_thumbnails()
    return min(timings), grid


def painted_tile(grid, row, selected):
    image = QImage(200, 200, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    option = QStyleOptionViewItem()
    option.rect = QRect(0, 0, 200, 200)
    if selected:
        option.state |= QStyle.StateFlag.State_Selected
    grid.itemDelegate().paint(painter, option, grid.model().index(row, 0))
    painter.end()
    return image


def test_the_tile_under_the_grid_cursor_is_painted_highlighted_so_the_cursor_can_be_seen(qtbot, tmp_path):
    touch(tmp_path, "a.jpg")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)

    corner = (10, 10)
    assert painted_tile(grid, 0, selected=True).pixelColor(*corner) != painted_tile(grid, 0, selected=False).pixelColor(*corner)


def test_in_a_folders_grid_an_image_tile_gets_its_thumbnail_once_generation_finishes(qtbot, tmp_path):
    image = QImage(800, 400, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.red)
    image.save(str(tmp_path / "photo.jpg"))
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    grid.show()
    tile = grid.model().index(0, 0).data(TILE_ROLE)

    qtbot.waitUntil(lambda: tile.thumbnail is not None)

    assert tile.thumbnail.size() == QSize(400, 200)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_in_a_folders_grid_a_video_tile_gets_its_thumbnail_and_its_duration(qtbot, tmp_path):
    make_clip(tmp_path / "clip.mp4", duration=3)
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    grid.show()
    tile = grid.model().index(0, 0).data(TILE_ROLE)

    qtbot.waitUntil(lambda: tile.thumbnail is not None)

    assert tile.thumbnail.size() == QSize(400, 300)
    assert tile.duration == pytest.approx(3, abs=0.2)


def test_in_a_folders_grid_a_folder_tile_gets_the_thumbnail_of_its_first_image(qtbot, tmp_path):
    (tmp_path / "trip").mkdir()
    image = QImage(1600, 800, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.red)
    image.save(str(tmp_path / "trip" / "photo.jpg"))
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    grid.show()
    tile = grid.model().index(0, 0).data(TILE_ROLE)

    qtbot.waitUntil(lambda: tile.thumbnail is not None)

    assert tile.thumbnail.size() == QSize(400, 200)


def test_in_a_folders_grid_a_folder_tile_with_no_image_directly_inside_keeps_no_thumbnail(qtbot, tmp_path):
    (tmp_path / "clips").mkdir()
    one_pixel_gif = base64.b64decode("R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==")
    (tmp_path / "clips" / "loop.gif").write_bytes(one_pixel_gif)  # a GIF is a video here, though Qt can read it as an image
    image = QImage(800, 400, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.red)
    image.save(str(tmp_path / "photo.jpg"))
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    grid.show()
    folder_tile = grid.model().index(0, 0).data(TILE_ROLE)
    image_tile = grid.model().index(1, 0).data(TILE_ROLE)

    qtbot.waitUntil(lambda: image_tile.thumbnail is not None)  # queued after the folder: its result has come in too

    assert folder_tile.thumbnail is None


def test_in_a_large_folders_grid_tiles_in_view_get_their_thumbnails_before_tiles_far_out_of_view(qtbot, tmp_path, monkeypatch):
    import threading

    from mediatagger import grid as grid_module

    lock = threading.Lock()
    started = []

    def generate(path):
        with lock:
            started.append(path)
        return None, None

    monkeypatch.setattr(grid_module, "thumbnail_and_duration", generate)
    names = [f"IMG_{i:04}.jpg" for i in range(1000)]
    touch(tmp_path, *names)
    in_view = tmp_path / names[-1]
    far_out_of_view = tmp_path / names[0]
    grid = Grid(tmp_path, at=in_view)
    qtbot.addWidget(grid)
    grid.resize(800, 600)
    grid.show()
    qtbot.waitExposed(grid)

    qtbot.waitUntil(lambda: in_view in started)

    with lock:
        assert far_out_of_view not in started[: started.index(in_view)]


def test_scrolling_a_large_folders_grid_makes_the_newly_visible_tiles_thumbnails_arrive_before_still_hidden_ones(qtbot, tmp_path, monkeypatch):
    import threading

    from mediatagger import grid as grid_module

    lock = threading.Lock()
    started = []
    scrolled = threading.Event()

    def generate(path):
        with lock:
            started.append(path)
        scrolled.wait(timeout=5)  # the workers' first thumbnails stay busy until the grid has been scrolled
        return None, None

    monkeypatch.setattr(grid_module, "thumbnail_and_duration", generate)
    names = [f"IMG_{i:04}.jpg" for i in range(1000)]
    touch(tmp_path, *names)
    newly_visible = tmp_path / names[-1]
    still_hidden = tmp_path / names[500]
    grid = Grid(tmp_path, at=tmp_path / names[0])
    qtbot.addWidget(grid)
    grid.resize(800, 600)
    grid.show()
    qtbot.waitExposed(grid)
    qtbot.waitUntil(lambda: len(started) == 3)

    grid.scrollToBottom()
    scrolled.set()
    qtbot.waitUntil(lambda: newly_visible in started)

    with lock:
        assert still_hidden not in started[: started.index(newly_visible)]


def test_a_thumbnail_arriving_reports_a_change_for_its_own_tiles_row_only(qtbot, tmp_path):
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        image = QImage(800, 400, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.red)
        image.save(str(tmp_path / name))
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    changed_rows = []
    grid.model().dataChanged.connect(lambda top_left, bottom_right: changed_rows.append((top_left.row(), bottom_right.row())))
    grid.show()
    tiles = [grid.model().index(row, 0).data(TILE_ROLE) for row in range(3)]

    qtbot.waitUntil(lambda: all(tile.thumbnail is not None for tile in tiles))

    assert sorted(changed_rows) == [(0, 0), (1, 1), (2, 2)]


def painted_red_area(image):
    """The bounding box of the red pixels painted on a tile, or None if there are none."""
    red = [(x, y) for y in range(image.height()) for x in range(image.width())
           if (lambda c: c.red() > 200 and c.green() < 60 and c.blue() < 60)(image.pixelColor(x, y))]
    if not red:
        return None
    xs, ys = [x for x, _ in red], [y for _, y in red]
    return QRect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


def test_a_tile_with_a_thumbnail_paints_the_picture_above_the_filename_aspect_ratio_kept(qtbot, tmp_path):
    touch(tmp_path, "photo.jpg")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    thumbnail = QImage(400, 200, QImage.Format.Format_RGB32)
    thumbnail.fill(Qt.GlobalColor.red)
    grid.model().index(0, 0).data(TILE_ROLE).thumbnail = thumbnail

    image = painted_tile(grid, 0, selected=False)
    filename_top = image.height() - QFontMetrics(QGuiApplication.font()).height()  # the filename is painted along the bottom
    picture = painted_red_area(image)

    assert picture is not None
    assert picture.width() / picture.height() == pytest.approx(2, rel=0.05)
    assert picture.bottom() < filename_top


def test_a_tile_paints_its_type_glyph_only_while_it_has_no_thumbnail(qtbot, tmp_path):
    touch(tmp_path, "photo.jpg")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    without_thumbnail = painted_texts(grid, 0)
    thumbnail = QImage(400, 200, QImage.Format.Format_RGB32)
    thumbnail.fill(Qt.GlobalColor.red)
    grid.model().index(0, 0).data(TILE_ROLE).thumbnail = thumbnail

    with_thumbnail = painted_texts(grid, 0)

    assert IMAGE_GLYPH in without_thumbnail
    assert IMAGE_GLYPH not in with_thumbnail


def test_a_video_tile_paints_its_duration_next_to_the_play_badge(qtbot, tmp_path):
    touch(tmp_path, "clip.mp4")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    grid.model().index(0, 0).data(TILE_ROLE).duration = 75

    texts = painted_texts(grid, 0)

    assert any(VIDEO_BADGE in text and format_duration(75) in text for text in texts)
