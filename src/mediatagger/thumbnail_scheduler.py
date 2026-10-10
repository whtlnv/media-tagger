import threading
from concurrent.futures import ThreadPoolExecutor


class ThumbnailScheduler:
    def __init__(self, generate):
        self._generate = generate
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._pending = []
        self._lock = threading.Lock()

    def request(self, path):
        with self._lock:
            already_pending = path in self._pending
            if already_pending:
                self._pending.remove(path)
            self._pending.append(path)
        if not already_pending:
            self._executor.submit(self._generate_most_recent)

    def _generate_most_recent(self):
        with self._lock:
            path = self._pending.pop()
        self._generate(path)
