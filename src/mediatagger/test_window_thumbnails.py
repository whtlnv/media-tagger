
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget

from mediatagger.grid import TILE_ROLE
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


def window_on_the_grid_of(qtbot, first_file):
    from mediatagger.test_viewer import show_exposed
    from mediatagger.test_window import shown_status_bar_texts

    window = Window(first_file, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    seen = []
    original = window.status_bar.show_background
    window.status_bar.show_background = lambda text, finished=False: (seen.append(text), original(text, finished))
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    return window, seen, lambda: shown_status_bar_texts(window)


def test_while_a_folders_thumbnails_generate_the_status_bar_counts_them_then_says_they_are_ready(qtbot, tmp_path):
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_image(tmp_path / name, "red")
    window, seen, shown = window_on_the_grid_of(qtbot, tmp_path / "a.jpg")

    qtbot.waitUntil(lambda: "✓ Thumbnails ready" in shown())

    import re

    generating = [text for text in seen if text.startswith("⟳")]
    assert generating and all(re.fullmatch(r"⟳ Generating thumbnails [0-2] / 3", text) for text in generating)


def test_opening_a_folder_whose_thumbnails_are_all_cached_shows_no_thumbnail_message(qtbot, tmp_path):
    for name in ("a.jpg", "b.jpg"):
        make_image(tmp_path / name, "red")
    window, seen, shown = window_on_the_grid_of(qtbot, tmp_path / "a.jpg")
    qtbot.waitUntil(lambda: "✓ Thumbnails ready" in shown())
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    seen.clear()

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    tile = stack.currentWidget().model().index(0, 0).data(TILE_ROLE)
    qtbot.waitUntil(lambda: tile.thumbnail is not None)
    qtbot.wait(200)

    assert [text for text in seen if "humbnail" in text] == []


def test_starting_a_slideshow_while_thumbnails_generate_takes_their_progress_off_the_status_bar(qtbot, tmp_path, monkeypatch):
    import threading

    from mediatagger import grid as grid_module

    release = threading.Event()
    monkeypatch.setattr(grid_module, "thumbnail_and_duration", lambda path: release.wait(timeout=10) and (None, None))
    for name in ("a.jpg", "b.jpg"):
        make_image(tmp_path / name, "red")
    window, seen, shown = window_on_the_grid_of(qtbot, tmp_path / "a.jpg")
    try:
        qtbot.waitUntil(lambda: any(text.startswith("⟳") for text in shown()))
        stack = window.findChild(QStackedWidget)
        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    finally:
        release.set()
    qtbot.wait(200)

    assert [text for text in shown() if "humbnail" in text] == []


def test_closing_the_window_stops_its_folder_grids_thumbnails_so_one_still_being_generated_reaches_no_tile(qtbot, tmp_path, monkeypatch):
    import threading

    from mediatagger import grid as grid_module
    from mediatagger.thumbnails import thumbnail_and_duration

    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def generate(path):
        started.set()
        release.wait(timeout=10)
        try:
            return thumbnail_and_duration(path)
        finally:
            finished.set()

    monkeypatch.setattr(grid_module, "thumbnail_and_duration", generate)
    make_image(tmp_path / "a.jpg", "red")
    window = Window(tmp_path / "a.jpg", player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    tile = stack.currentWidget().model().index(0, 0).data(TILE_ROLE)
    qtbot.waitUntil(started.is_set)

    window.close()
    release.set()
    qtbot.waitUntil(finished.is_set)
    qtbot.wait(200)  # long enough for a finished thumbnail to be delivered to its tile

    assert tile.thumbnail is None


def test_closing_the_window_stops_its_results_grids_thumbnails_so_one_still_being_generated_reaches_no_tile(qtbot, tmp_path, monkeypatch):
    import threading

    from mediatagger import grid as grid_module
    from mediatagger.library import Library
    from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
    from mediatagger.test_window import window_showing_the_grid_with_its_cursor_on_its_first_tile
    from mediatagger.test_window_search import search_for
    from mediatagger.thumbnails import thumbnail_and_duration

    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    result = drive / "Elsewhere" / "IMG_9.png"
    result.parent.mkdir()
    make_image(result, "blue")
    Library.open(drive).enter(result, "beach")
    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def generate(path):
        if path != result:
            return thumbnail_and_duration(path)
        started.set()
        release.wait(timeout=10)
        try:
            return thumbnail_and_duration(path)
        finally:
            finished.set()

    monkeypatch.setattr(grid_module, "thumbnail_and_duration", generate)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")
    tile = stack.currentWidget().model().index(0, 0).data(TILE_ROLE)
    qtbot.waitUntil(started.is_set)

    window.close()
    release.set()
    qtbot.waitUntil(finished.is_set)
    qtbot.wait(200)  # long enough for a finished thumbnail to be delivered to its tile

    assert (tile.path, tile.thumbnail) == (result, None)
