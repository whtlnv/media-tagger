import threading
from concurrent.futures import ThreadPoolExecutor

import PySide6.QtCore
import PySide6.QtGui
from PySide6.QtCore import QCoreApplication, QObject, Signal

WORKERS = 3


class _Generated(QObject):
    done = Signal(object, object)
    prefetched = Signal(object, object)
    surveyed = Signal(object)


def _create_qt_types_on_this_thread():
    """PySide creates a module's Python types lazily, the first time each is used, and that creation is not
    thread-safe: workers constructing their first QImageReader side by side crashed the app inside Shiboken. So every
    QtCore and QtGui type (all the workers' code may touch) is created here, on the GUI thread, before any worker runs.
    Once per process; about 0.1 s."""
    for module in (PySide6.QtCore, PySide6.QtGui):
        for name in dir(module):
            getattr(module, name)


class _Work:
    """What the workers share with the GUI thread: the queues, and the Qt object results are posted through. The
    workers hold this, never the scheduler, and the Qt object belongs to a GUI-thread parent, so a worker dropping
    its reference can never destroy it off the GUI thread."""

    def __init__(self, generate, prefetch, emitter):
        self.generate = generate
        self.prefetch = prefetch
        self.emitter = emitter
        self.pending = []
        self.unrequested = {}  # the rest of the folder, in order; a dict so a request finds and withdraws one at once
        self.generating = set()  # never started twice at once
        self.stopped = False
        self.workers = 0
        self.lock = threading.Lock()

    def run(self):
        """One worker: generates until nothing is left, so a folder of thousands costs a few tasks, not one each."""
        while (taken := self._take_next()) is not None:
            path, requested = taken
            requested = requested or self.prefetch is None  # with no prefetch of its own, the rest is generated like requests
            try:
                outcome = (self.generate if requested else self.prefetch)(path)
            except Exception:  # one unreadable file must not take its worker, and the rest of the folder, down with it
                outcome = None
            with self.lock:  # held while posting, so the emitter cannot be destroyed mid-emit once stopped
                self.generating.discard(path)
                if not self.stopped:
                    (self.emitter.done if requested else self.emitter.prefetched).emit(path, outcome)

    def _take_next(self):
        with self.lock:
            if self.stopped or not (self.pending or self.unrequested):
                self.workers -= 1
                return None
            requested = bool(self.pending)
            path = self.pending.pop() if requested else self._take_first_unrequested()
            self.generating.add(path)
            return path, requested

    def _take_first_unrequested(self):
        path = next(iter(self.unrequested))
        del self.unrequested[path]
        return path

    def needs_a_worker(self):
        """Called with the lock held, after queueing work: whether another worker should start."""
        if self.stopped or self.workers >= WORKERS:
            return False
        self.workers += 1
        return True

    def survey(self, function):
        result = function()
        with self.lock:
            if not self.stopped:
                self.emitter.surveyed.emit(result)

    def stop(self):
        with self.lock:
            self.stopped = True
            self.pending.clear()
            self.unrequested.clear()


class ThumbnailScheduler:
    _qt_types_created = False

    def __init__(self, generate, parent=None, prefetch=None):
        """Requested files go through `generate` and come back through `generated`. The rest of the folder goes
        through `prefetch`, if given, and comes back through `prefetched`; else it is generated like a request."""
        if not ThumbnailScheduler._qt_types_created:
            _create_qt_types_on_this_thread()
            ThumbnailScheduler._qt_types_created = True
        emitter = _Generated(parent or QCoreApplication.instance())
        self.generated = emitter.done
        self.prefetched = emitter.prefetched
        self.surveyed = emitter.surveyed
        self._work = _Work(generate, prefetch, emitter)
        work = self._work
        emitter.destroyed.connect(lambda: work.stop())  # its parent went first: nothing may be posted through it any more
        self._executor = ThreadPoolExecutor(max_workers=WORKERS)
        self._surveyor = ThreadPoolExecutor(max_workers=1)  # beside the workers, which may all be busy for a while

    def enter_folder(self, paths):
        """Queues the rest of the folder, behind every request, skipping what is already being generated."""
        with self._work.lock:
            self._work.unrequested = dict.fromkeys(path for path in paths if path not in self._work.generating)
        self._start_workers()

    def request(self, path):
        with self._work.lock:
            if path in self._work.generating:
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

    def survey(self, function):
        """Runs `function` on a thread of its own and sends its result back through `surveyed`."""
        with self._work.lock:
            if self._work.stopped:
                return
        self._surveyor.submit(self._work.survey, function)

    def shut_down(self):
        """Drops pending work, lets running work finish without delivering, and frees the Qt object on the GUI thread."""
        self._work.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)
        self._surveyor.shutdown(wait=False, cancel_futures=True)
        self._work.emitter.deleteLater()

    def _withdraw(self, path):
        if path in self._work.pending:  # a handful of requests: a list is quick
            self._work.pending.remove(path)
        self._work.unrequested.pop(path, None)
