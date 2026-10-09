import gc

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

GARBAGE_COLLECTION_MS = 500


def collect_garbage_on_the_gui_thread():
    """Python's collector runs on whichever thread allocates, often mpv's event thread. A widget it frees there is
    destroyed off the GUI thread, possibly mid-paint, which crashes. So collect only from a GUI-thread timer."""
    app = QApplication.instance()
    if app.property("mediatagger_gc_timer"):
        return
    gc.disable()
    timer = QTimer(app)
    timer.timeout.connect(_collect_due_generation)
    timer.start(GARBAGE_COLLECTION_MS)
    app.setProperty("mediatagger_gc_timer", True)


def _collect_due_generation():
    """The oldest generation past its threshold, as Python's automatic collection would choose."""
    due = [generation for generation, (count, threshold) in enumerate(zip(gc.get_count(), gc.get_threshold())) if count > threshold]
    gc.collect(due[-1] if due else 0)
