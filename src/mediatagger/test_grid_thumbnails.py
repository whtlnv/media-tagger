import base64
import shutil

import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage

from mediatagger.grid import TILE_ROLE, Grid
from mediatagger.test_folder import touch
from mediatagger.test_video import make_clip
from mediatagger.test_viewer import make_image


def test_in_a_folders_grid_an_image_tile_gets_its_thumbnail_once_generation_finishes(qtbot, tmp_path):
    make_image(tmp_path / "photo.jpg", "red", width=800, height=400)
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
    make_image(tmp_path / "trip" / "photo.jpg", "red", width=1600, height=800)
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
    make_image(tmp_path / "photo.jpg", "red", width=800, height=400)
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    grid.resize(800, 600)  # both tiles in view: only those get their pictures
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
        make_image(tmp_path / name, "red", width=800, height=400)
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    changed_rows = []
    grid.model().dataChanged.connect(lambda top_left, bottom_right: changed_rows.append((top_left.row(), bottom_right.row())))
    grid.resize(800, 600)  # every tile in view: only those get their pictures
    grid.show()
    tiles = [grid.model().index(row, 0).data(TILE_ROLE) for row in range(3)]

    qtbot.waitUntil(lambda: all(tile.thumbnail is not None for tile in tiles))

    assert sorted(changed_rows) == [(0, 0), (1, 1), (2, 2)]


def test_tiles_out_of_view_let_go_of_their_pictures_beyond_the_ones_the_grid_holds(qtbot, tmp_path, monkeypatch):
    from mediatagger import grid as grid_module

    monkeypatch.setattr(grid_module, "HELD_THUMBNAILS", 4)
    monkeypatch.setattr(grid_module, "thumbnail_and_duration", lambda path: (QImage(40, 40, QImage.Format.Format_RGB32), None))
    touch(tmp_path, *[f"IMG_{i:02}.jpg" for i in range(40)])
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)
    grid.resize(450, 250)  # two tiles in view
    grid.show()
    tiles = [grid.model().index(row, 0).data(TILE_ROLE) for row in range(40)]
    qtbot.waitUntil(lambda: tiles[0].thumbnail is not None)

    for row in range(0, 40, 2):
        grid.scrollTo(grid.model().index(row, 0))
        qtbot.waitUntil(lambda: tiles[row].thumbnail is not None)

    holding = [row for row, tile in enumerate(tiles) if tile.thumbnail is not None]
    assert (len(holding) <= 4, tiles[38].thumbnail is not None) == (True, True)
