from PySide6.QtCore import QObject
from PySide6.QtGui import QColor, QImage

from mediatagger.folder_thumbnails import FolderThumbnails
from mediatagger.thumbnail_cache import ThumbnailCache


def solid(color):
    image = QImage(400, 200, QImage.Format.Format_RGB32)
    image.fill(QColor(color))
    return image


def folder_of(tmp_path, *names):
    paths = [tmp_path / name for name in names]
    for path in paths:
        path.write_bytes(b"media")
    return paths


def test_a_requested_files_thumbnail_and_duration_arrive_on_the_gui_thread(qtbot, tmp_path):
    [clip] = folder_of(tmp_path, "clip.mp4")
    owner = QObject()
    thumbnails = FolderThumbnails([clip], ThumbnailCache(":memory:"), owner, generate=lambda path: (solid("blue"), 42.0))
    arrived = []
    thumbnails.arrived.connect(lambda path, thumbnail, duration: arrived.append((path, thumbnail.pixelColor(0, 0).name(), duration)))

    thumbnails.start()
    thumbnails.request(clip)
    qtbot.waitUntil(lambda: len(arrived) == 1)

    assert arrived == [(clip, "#0000ff", 42.0)]


def test_a_thumbnail_already_generating_when_its_folder_is_left_still_finishes_and_is_cached(qtbot, tmp_path):
    import threading

    [photo] = folder_of(tmp_path, "photo.jpg")
    started = threading.Event()
    release = threading.Event()

    def generate(path):
        started.set()
        release.wait(timeout=10)
        return solid("red"), None

    cache = ThumbnailCache(":memory:")
    owner = QObject()
    thumbnails = FolderThumbnails([photo], cache, owner, generate=generate)
    try:
        thumbnails.request(photo)
        qtbot.waitUntil(started.is_set)
        thumbnails.stop()
    finally:
        release.set()

    stat = photo.stat()
    qtbot.waitUntil(lambda: cache.lookup(photo, stat.st_size, stat.st_mtime) is not None)
    assert cache.lookup(photo, stat.st_size, stat.st_mtime).pixelColor(0, 0).name() == "#ff0000"


def test_a_folder_whose_thumbnails_are_all_cached_generates_nothing_and_reports_no_progress(qtbot, tmp_path):
    paths = folder_of(tmp_path, "a.jpg", "b.jpg", "c.jpg")
    cache = ThumbnailCache(":memory:")
    for path in paths:
        cache.store(path, path.stat().st_size, path.stat().st_mtime, solid("red"))
    generated = []
    owner = QObject()
    thumbnails = FolderThumbnails(paths, cache, owner, generate=lambda path: generated.append(path) or (solid("blue"), None))
    progress = []
    arrived = []
    thumbnails.progress.connect(lambda done, total: progress.append((done, total)))
    thumbnails.arrived.connect(lambda path, thumbnail, duration: arrived.append(path))

    thumbnails.start()
    for path in paths:
        thumbnails.request(path)
    qtbot.waitUntil(lambda: len(arrived) == 3)
    qtbot.wait(100)

    assert (generated, progress) == ([], [])

