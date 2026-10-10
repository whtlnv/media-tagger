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
