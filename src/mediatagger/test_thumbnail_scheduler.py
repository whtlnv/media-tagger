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
