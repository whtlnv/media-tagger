import threading
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, Signal


class _Generated(QObject):
    done = Signal(object, object)


def _store(cache, path, thumbnail):
    stat = path.stat()
    cache.store(path, stat.st_size, stat.st_mtime, thumbnail)


class ThumbnailScheduler:
    def __init__(self, generate, cache=None):
        self._generate = generate
        self._cache = cache
        self._generated = _Generated()
        self.generated = self._generated.done
        if cache is not None:
            self._generated.done.connect(lambda path, thumbnail: _store(cache, path, thumbnail))
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._pending = []
        self._unrequested = []
        self._taken = set()  # started or done: never generated twice
        self._lock = threading.Lock()

    def enter_folder(self, paths):
        with self._lock:
            self._pending = []
            self._unrequested = list(paths)
        for _ in paths:
            self._executor.submit(self._generate_next)

    def request(self, path):
        if self._cache is not None:
            stat = path.stat()
            if self._cache.lookup(path, stat.st_size, stat.st_mtime) is not None:
                return
        with self._lock:
            if path in self._taken:
                return
            already_queued = self._withdraw(path)
            self._pending.append(path)
        if not already_queued:
            self._executor.submit(self._generate_next)

    def _withdraw(self, path):
        queues = [queue for queue in (self._pending, self._unrequested) if path in queue]
        for queue in queues:
            queue.remove(path)
        return bool(queues)

    def _generate_next(self):
        with self._lock:
            path = self._pending.pop() if self._pending else self._unrequested.pop(0)
            self._taken.add(path)
        self._generated.done.emit(path, self._generate(path))
