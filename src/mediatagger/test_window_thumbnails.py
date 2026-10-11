
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget

from mediatagger.test_folder import touch
from mediatagger.test_viewer import SILENT, make_image
from mediatagger.window import Window


def test_starting_a_slideshow_from_the_windows_grid_stops_generating_that_folders_pending_thumbnails(qtbot, tmp_path, monkeypatch):
    import threading

    from mediatagger import grid as grid_module

    lock = threading.Lock()
    started = []
    finished = []
    release = threading.Event()

    def generate(path):
        with lock:
            started.append(path)
        release.wait(timeout=10)
        with lock:
            finished.append(path)
        return None, None

    monkeypatch.setattr(grid_module, "thumbnail_and_duration", generate)
    make_image(tmp_path / "a.jpg", "red")
    touch(tmp_path, *(f"IMG_{i:02}.jpg" for i in range(20)))
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: len(started) == 3)
    busy = list(started)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    release.set()
    qtbot.waitUntil(lambda: all(path in finished for path in busy))
    qtbot.wait(200)  # long enough for a worker still fed by the grid to start its next thumbnail

    with lock:
        assert started == busy


def test_going_in_and_out_of_a_subfolder_many_times_leaves_no_thumbnail_workers_behind(qtbot, tmp_path):
    import threading

    (tmp_path / "day1").mkdir()
    make_image(tmp_path / "day1" / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path / "b.jpg", player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.wait(200)
    before = threading.active_count()

    for _ in range(10):
        stack.currentWidget().setCurrentIndex(stack.currentWidget().model().index(0, 0))
        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
        qtbot.wait(50)
        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Backspace)
        qtbot.wait(50)
    qtbot.waitUntil(lambda: threading.active_count() <= before + 3, timeout=3000)


def test_opening_a_folders_grid_a_second_time_generates_nothing(qtbot, tmp_path, monkeypatch):
    from mediatagger import grid as grid_module
    from mediatagger.grid import TILE_ROLE
    from mediatagger.thumbnails import thumbnail_and_duration

    generated = []

    def generate(path):
        generated.append(path)
        return thumbnail_and_duration(path)

    monkeypatch.setattr(grid_module, "thumbnail_and_duration", generate)
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path / "b.jpg", player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    first_tile = stack.currentWidget().model().index(0, 0).data(TILE_ROLE)
    qtbot.waitUntil(lambda: first_tile.thumbnail is not None)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.wait(200)  # long enough for the second grid's workers to start generating

    assert generated == [tmp_path / "b.jpg"]


def test_on_a_drive_with_a_library_the_grids_thumbnails_are_written_to_that_drives_cache(qtbot, tmp_path):
    import os
    import sqlite3
    from pathlib import Path

    from mediatagger.grid import TILE_ROLE
    from mediatagger.library import Library
    from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image

    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    tile = stack.currentWidget().model().index(0, 0).data(TILE_ROLE)
    qtbot.waitUntil(lambda: tile.thumbnail is not None)

    thumbs_db = Path(os.environ["XDG_CACHE_HOME"]) / "mediatagger" / Library.open(drive).drive_id / "thumbs.db"
    connection = sqlite3.connect(thumbs_db)
    stored = [path for (path,) in connection.execute("SELECT path FROM thumbnails")]
    connection.close()
    assert stored == ["Photos/IMG_1.png"]


def test_on_the_system_disk_the_grids_thumbnails_are_written_nowhere_on_disk(qtbot, tmp_path):
    import os
    from pathlib import Path

    from mediatagger.grid import TILE_ROLE

    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path / "b.jpg", player_options=SILENT, is_mount_point=lambda path: path == Path("/"))
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    tile = stack.currentWidget().model().index(0, 0).data(TILE_ROLE)
    qtbot.waitUntil(lambda: tile.thumbnail is not None)

    assert list(Path(os.environ["XDG_CACHE_HOME"]).rglob("*")) == []
