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
