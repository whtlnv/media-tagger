from PySide6.QtCore import QEvent, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel


HIDE_DELAY_MS = 3000  # the bar fades after this long without input


class ProgressBar(QLabel):
    """A video's progress, shown only while the video surface it follows is shown."""

    def __init__(self, parent, hide_delay=HIDE_DELAY_MS):
        super().__init__(parent)
        self._ticker = QTimer(self, interval=250, timeout=self._tick)
        self._hide_timer = QTimer(self, interval=hide_delay, singleShot=True, timeout=self.hide)
        self._playing = False
        self.hide()

    def follow(self, surface):
        surface.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Hide and watched.isHidden():  # the surface itself, not a hidden ancestor
            self._playing = False
            self.hide()
        return False

    def start(self, engine):
        self._engine = engine
        self._show_elapsed(0)
        self._playing = True
        self.wake()

    def wake(self):
        """Show the bar for another hide delay, if a video is playing."""
        if not self._playing:
            return
        self._ticker.start()
        self._hide_timer.start()
        self.show()

    def _tick(self):
        if not self.isVisible():  # hidden, or its viewer closed: mpv may be gone, so don't ask it
            self._ticker.stop()
            return
        if self._engine.time_pos is None:  # mpv has no position while a clip loads or stops
            return
        self._show_elapsed(int(self._engine.time_pos))

    def _show_elapsed(self, seconds):
        duration = self._engine.duration
        self._fraction = seconds / duration
        with_hours = duration >= 60 * 60
        self.setText(f"{_clock(seconds, with_hours)} / {_clock(duration, with_hours)}")

    def paintEvent(self, event):
        with QPainter(self) as painter:
            filled_width = int(self.width() * self._fraction)
            painter.fillRect(0, 0, filled_width, self.height(), self.palette().highlight())
        super().paintEvent(event)


def _clock(seconds, with_hours):
    minutes, seconds = divmod(round(seconds), 60)
    if with_hours:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"
