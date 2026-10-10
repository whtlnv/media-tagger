import threading
from concurrent.futures import ThreadPoolExecutor


class ThumbnailScheduler:
    def __init__(self, generate):
        self._generate = generate
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._pending = []
        self._unrequested = []
        self._lock = threading.Lock()

    def enter_folder(self, paths):
        with self._lock:
            self._unrequested = list(paths)
        for _ in paths:
            self._executor.submit(self._generate_next)

    def request(self, path):
        with self._lock:
            already_queued = path in self._pending or path in self._unrequested
            if path in self._pending:
                self._pending.remove(path)
            if path in self._unrequested:
                self._unrequested.remove(path)
            self._pending.append(path)
        if not already_queued:
            self._executor.submit(self._generate_next)

    def _generate_next(self):
        with self._lock:
            path = self._pending.pop() if self._pending else self._unrequested.pop(0)
        self._generate(path)
