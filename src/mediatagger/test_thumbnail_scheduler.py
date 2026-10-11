import threading

from mediatagger.thumbnail_scheduler import ThumbnailScheduler


def test_with_more_than_three_thumbnails_pending_exactly_three_generate_at_once(qtbot, tmp_path):
    lock = threading.Lock()
    release = threading.Event()
    running = 0
    peak = 0
    generated = []

    def generate(path):
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        release.wait(timeout=10)
        with lock:
            running -= 1
            generated.append(path)

    scheduler = ThumbnailScheduler(generate=generate)
    paths = [tmp_path / f"{index}.jpg" for index in range(5)]
    try:
        for path in paths:
            scheduler.request(path)
        qtbot.waitUntil(lambda: running == 3)
    finally:
        release.set()
    qtbot.waitUntil(lambda: len(generated) == 5)

    assert peak == 3


def test_while_workers_are_busy_the_most_recently_requested_thumbnail_is_generated_first(qtbot, tmp_path):
    lock = threading.Lock()
    started = []
    generated = []

    def generate(path):
        with lock:
            started.append(path)
        releases[path].wait(timeout=10)
        with lock:
            generated.append(path)

    scheduler = ThumbnailScheduler(generate=generate)
    busy = [tmp_path / f"busy{index}.jpg" for index in range(3)]
    pending = [tmp_path / f"pending{index}.jpg" for index in range(3)]
    releases = {path: threading.Event() for path in busy + pending}
    try:
        for path in busy:
            scheduler.request(path)
        qtbot.waitUntil(lambda: len(started) == 3)
        for path in pending:
            scheduler.request(path)
        releases[busy[0]].set()
        qtbot.waitUntil(lambda: len(started) == 4)
    finally:
        for event in releases.values():
            event.set()
    qtbot.waitUntil(lambda: len(generated) == 6)

    assert started[3] == pending[-1]


def test_re_requesting_a_pending_thumbnail_moves_it_ahead_of_the_others(qtbot, tmp_path):
    lock = threading.Lock()
    started = []
    generated = []

    def generate(path):
        with lock:
            started.append(path)
        releases[path].wait(timeout=10)
        with lock:
            generated.append(path)

    scheduler = ThumbnailScheduler(generate=generate)
    busy = [tmp_path / f"busy{index}.jpg" for index in range(3)]
    pending = [tmp_path / f"pending{index}.jpg" for index in range(3)]
    releases = {path: threading.Event() for path in busy + pending}
    for path in pending:
        releases[path].set()
    try:
        for path in busy:
            scheduler.request(path)
        qtbot.waitUntil(lambda: len(started) == 3)
        for path in pending:
            scheduler.request(path)
        scheduler.request(pending[1])
        releases[busy[0]].set()
        qtbot.waitUntil(lambda: len(started) >= 6)
        with lock:
            order = started[3:6]
    finally:
        for event in releases.values():
            event.set()
    qtbot.waitUntil(lambda: len(generated) >= 6)

    assert order == [pending[1], pending[2], pending[0]]


def test_once_requested_thumbnails_are_done_the_rest_of_the_folder_is_generated_unrequested(qtbot, tmp_path):
    lock = threading.Lock()
    generated = []

    def generate(path):
        with lock:
            generated.append(path)

    scheduler = ThumbnailScheduler(generate=generate)
    folder = [tmp_path / f"{index}.jpg" for index in range(6)]
    scheduler.enter_folder(folder)
    scheduler.request(folder[2])
    qtbot.waitUntil(lambda: len(generated) == len(folder))

    assert sorted(generated) == sorted(folder)


def test_a_thumbnail_requested_while_it_is_generating_is_not_generated_again(qtbot, tmp_path):
    lock = threading.Lock()
    release = threading.Event()
    started = []

    def generate(path):
        with lock:
            started.append(path)
        release.wait(timeout=10)

    scheduler = ThumbnailScheduler(generate=generate)
    path = tmp_path / "busy.jpg"
    try:
        scheduler.request(path)
        qtbot.waitUntil(lambda: len(started) == 1)
        scheduler.request(path)
        qtbot.wait(200)
    finally:
        release.set()

    assert started == [path]


def test_a_thumbnail_requested_while_the_folder_is_prefetching_is_generated_before_the_remaining_prefetch(qtbot, tmp_path):
    lock = threading.Lock()
    started = []
    generated = []

    def generate(path):
        with lock:
            started.append(path)
        releases[path].wait(timeout=10)
        with lock:
            generated.append(path)

    scheduler = ThumbnailScheduler(generate=generate)
    folder = [tmp_path / f"{index}.jpg" for index in range(8)]
    releases = {path: threading.Event() for path in folder}
    for path in folder[3:]:
        releases[path].set()
    try:
        scheduler.enter_folder(folder)
        qtbot.waitUntil(lambda: len(started) == 3)
        scheduler.request(folder[6])
        releases[started[0]].set()
        qtbot.waitUntil(lambda: len(started) >= 4)
        with lock:
            fourth = started[3]
    finally:
        for event in releases.values():
            event.set()
    qtbot.waitUntil(lambda: len(generated) == len(folder))

    assert fourth == folder[6]


def test_leaving_a_folder_drops_its_pending_thumbnails_so_they_are_never_generated(qtbot, tmp_path):
    lock = threading.Lock()
    started = []
    generated = []

    def generate(path):
        with lock:
            started.append(path)
        if path in busy:
            release.wait(timeout=10)
        with lock:
            generated.append(path)

    scheduler = ThumbnailScheduler(generate=generate)
    release = threading.Event()
    busy = [tmp_path / "left" / f"busy{index}.jpg" for index in range(3)]
    pending = [tmp_path / "left" / f"pending{index}.jpg" for index in range(3)]
    next_folder = [tmp_path / "next" / f"{index}.jpg" for index in range(2)]
    try:
        scheduler.enter_folder(busy + pending)
        qtbot.waitUntil(lambda: len(started) == 3)
        for path in pending:
            scheduler.request(path)
        scheduler.enter_folder(next_folder)
    finally:
        release.set()
    qtbot.waitUntil(lambda: all(path in generated for path in next_folder))

    assert not set(pending) & set(generated)


def test_a_thumbnail_already_generating_when_its_folder_is_left_still_finishes_and_is_cached(qtbot, tmp_path):
    from PySide6.QtGui import QColor, QImage

    from mediatagger.thumbnail_cache import ThumbnailCache

    started = threading.Event()
    release = threading.Event()

    def generate(path):
        started.set()
        release.wait(timeout=10)
        thumbnail = QImage(400, 200, QImage.Format_RGB32)
        thumbnail.fill(QColor("red"))
        return thumbnail

    (tmp_path / "left").mkdir()
    busy = tmp_path / "left" / "busy.jpg"
    busy.write_bytes(b"photo")
    stat = busy.stat()
    cache = ThumbnailCache(":memory:", root=tmp_path)
    scheduler = ThumbnailScheduler(generate=generate, cache=cache)
    try:
        scheduler.enter_folder([busy])
        qtbot.waitUntil(started.is_set)
        scheduler.enter_folder([])
    finally:
        release.set()
    qtbot.waitUntil(lambda: cache.lookup(busy, size=stat.st_size, mtime=stat.st_mtime) is not None)

    assert cache.lookup(busy, size=stat.st_size, mtime=stat.st_mtime).pixelColor(200, 100) == QColor("red")


def test_generated_thumbnails_are_delivered_on_the_gui_thread(qtbot, tmp_path):
    delivered = []

    def generate(path):
        return f"thumbnail of {path.name}"

    scheduler = ThumbnailScheduler(generate=generate)
    scheduler.generated.connect(
        lambda path, thumbnail: delivered.append((path, thumbnail, threading.current_thread()))
    )
    path = tmp_path / "photo.jpg"
    scheduler.request(path)
    qtbot.waitUntil(lambda: len(delivered) == 1)

    assert delivered == [(path, "thumbnail of photo.jpg", threading.main_thread())]
