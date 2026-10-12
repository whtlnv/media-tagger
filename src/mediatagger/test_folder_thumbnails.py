from PySide6.QtCore import QObject

from mediatagger.folder_thumbnails import FolderThumbnails
from mediatagger.test_thumbnail_cache import solid_thumbnail
from mediatagger.test_thumbnail_cache import solid_colour
from mediatagger.thumbnail_cache import ThumbnailCache


def folder_of(tmp_path, *names):
    paths = [tmp_path / name for name in names]
    for path in paths:
        path.write_bytes(b"media")
    return paths


def test_a_requested_files_thumbnail_and_duration_arrive_on_the_gui_thread(qtbot, tmp_path):
    [clip] = folder_of(tmp_path, "clip.mp4")
    owner = QObject()
    thumbnails = FolderThumbnails([clip], ThumbnailCache(":memory:"), owner, generate=lambda path: (solid_thumbnail("blue"), 42.0))
    arrived = []
    thumbnails.arrived.connect(lambda path, thumbnail, duration: arrived.append((path, solid_colour(thumbnail.pixelColor(0, 0)).name(), duration)))

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
        return solid_thumbnail("red"), None

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
    assert solid_colour(cache.lookup(photo, stat.st_size, stat.st_mtime).pixelColor(0, 0)).name() == "#ff0000"


def test_a_folder_whose_thumbnails_are_all_cached_generates_nothing_and_reports_no_progress(qtbot, tmp_path):
    paths = folder_of(tmp_path, "a.jpg", "b.jpg", "c.jpg")
    cache = ThumbnailCache(":memory:")
    for path in paths:
        cache.store(path, path.stat().st_size, path.stat().st_mtime, solid_thumbnail("red"))
    generated = []
    owner = QObject()
    thumbnails = FolderThumbnails(paths, cache, owner, generate=lambda path: generated.append(path) or (solid_thumbnail("blue"), None))
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



def test_progress_counts_only_the_thumbnails_that_had_to_be_generated(qtbot, tmp_path):
    cached, new, other = folder_of(tmp_path, "cached.jpg", "new.jpg", "other.jpg")
    cache = ThumbnailCache(":memory:")
    cache.store(cached, cached.stat().st_size, cached.stat().st_mtime, solid_thumbnail("red"))
    owner = QObject()
    thumbnails = FolderThumbnails([cached, new, other], cache, owner, generate=lambda path: (solid_thumbnail("blue"), None))
    progress = []
    thumbnails.progress.connect(lambda done, total: progress.append((done, total)))

    thumbnails.start()
    qtbot.waitUntil(lambda: progress[-1:] == [(2, 2)])

    assert progress[0] == (0, 2)


def test_a_total_of_1204_thumbnails_reads_with_thousands_separated():
    from mediatagger.folder_thumbnails import progress_text

    assert progress_text(132, 1204) == "⟳ Generating thumbnails 132 / 1,204"


def test_stopping_a_folders_thumbnails_a_second_time_after_qt_has_processed_deferred_deletions_raises_nothing(qtbot, tmp_path):
    from PySide6.QtCore import QCoreApplication, QEvent

    [photo] = folder_of(tmp_path, "photo.jpg")
    owner = QObject()
    thumbnails = FolderThumbnails([photo], ThumbnailCache(":memory:"), owner, generate=lambda path: (solid_thumbnail("red"), None))
    thumbnails.stop()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    thumbnails.stop()
