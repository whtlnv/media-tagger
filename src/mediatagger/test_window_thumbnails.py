
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
