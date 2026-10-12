from PySide6.QtCore import QEvent, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel


class ProgressBar(QLabel):
    """A video's progress, shown only while the video surface it follows is shown."""

    def __init__(self, parent):
        super().__init__(parent)
        self._ticker = QTimer(self, interval=250, timeout=self._tick)
        self.hide()

    def follow(self, surface):
        surface.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Hide and watched.isHidden():  # the surface itself, not a hidden ancestor
            self.hide()
        return False

    def hideEvent(self, event):
        self._ticker.stop()  # also when the viewer closes, before its mpv engine is gone

    def start(self, engine):
        self._engine = engine
        self._show_elapsed(0)
        self._ticker.start()
        self.show()

    def _tick(self):
        if self._engine.time_pos is None:  # mpv has no position while a clip loads or stops
            return
        self._show_elapsed(int(self._engine.time_pos))

    def _show_elapsed(self, seconds):
        self._fraction = seconds / self._engine.duration
        self.setText(f"{_clock(seconds)} / {_clock(self._engine.duration)}")

    def paintEvent(self, event):
        with QPainter(self) as painter:
            painter.fillRect(0, 0, int(self.width() * self._fraction), self.height(), self.palette().highlight())
        super().paintEvent(event)


def _clock(seconds):
    minutes, seconds = divmod(round(seconds), 60)
    return f"{minutes}:{seconds:02d}"
