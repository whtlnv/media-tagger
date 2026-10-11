import threading
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QCoreApplication, QObject, Signal

WORKERS = 3


class _Generated(QObject):
    done = Signal(object, object)


def _store(cache, path, thumbnail):
    stat = path.stat()
    cache.store(path, stat.st_size, stat.st_mtime, thumbnail)


def _is_cached(cache, path):
    stat = path.stat()
    return cache.lookup(path, stat.st_size, stat.st_mtime) is not None


class _Work:
    """What the workers share with the GUI thread: the queues, and the Qt object results are posted through. The
    workers hold this, never the scheduler, and the Qt object belongs to a GUI-thread parent, so a worker dropping
    its reference can never destroy it off the GUI thread."""

    def __init__(self, generate, emitter):
        self.generate = generate
        self.emitter = emitter
        self.pending = []
        self.unrequested = []
        self.taken = set()  # started or done: never generated twice
        self.stopped = False
        self.workers = 0
        self.lock = threading.Lock()

    def run(self):
        """One worker: generates until nothing is left, so a folder of thousands costs a few tasks, not one each."""
        while (path := self._take_next()) is not None:
            try:
                thumbnail = self.generate(path)
            except Exception:  # one unreadable file must not take its worker, and the rest of the folder, down with it
                thumbnail = None
            with self.lock:  # held while posting, so the emitter cannot be destroyed mid-emit once stopped
                if not self.stopped:
                    self.emitter.done.emit(path, thumbnail)

    def _take_next(self):
        with self.lock:
            if self.stopped or not (self.pending or self.unrequested):
                self.workers -= 1
                return None
            path = self.pending.pop() if self.pending else self.unrequested.pop(0)
            self.taken.add(path)
            return path

    def needs_a_worker(self):
        """Called with the lock held, after queueing work: whether another worker should start."""
        if self.stopped or self.workers >= WORKERS:
            return False
        self.workers += 1
        return True

    def stop(self):
        with self.lock:
            self.stopped = True
            self.pending.clear()
            self.unrequested.clear()


class ThumbnailScheduler:
    def __init__(self, generate, cache=None, parent=None):
        self._cache = cache
        emitter = _Generated(parent or QCoreApplication.instance())
        self.generated = emitter.done
        if cache is not None:
            emitter.done.connect(lambda path, thumbnail: _store(cache, path, thumbnail))
        self._work = _Work(generate, emitter)
        work = self._work
        emitter.destroyed.connect(lambda: work.stop())  # its parent went first: nothing may be posted through it any more
        self._executor = ThreadPoolExecutor(max_workers=WORKERS)

    def enter_folder(self, paths):
        with self._work.lock:
            self._work.pending = []
            self._work.unrequested = list(paths)
        self._start_workers()

    def request(self, path):
        if self._cache is not None and _is_cached(self._cache, path):
            return
        with self._work.lock:
            if path in self._work.taken:
                return
            self._withdraw(path)
            self._work.pending.append(path)
        self._start_workers()

    def _start_workers(self):
        while True:
            with self._work.lock:
                if not self._work.needs_a_worker():
                    return
            self._executor.submit(self._work.run)

    def shut_down(self):
        """Drops pending work, lets running work finish without delivering, and frees the Qt object on the GUI thread."""
        self._work.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)
        self._work.emitter.deleteLater()

    def _withdraw(self, path):
        for queue in (self._work.pending, self._work.unrequested):
            if path in queue:
                queue.remove(path)
