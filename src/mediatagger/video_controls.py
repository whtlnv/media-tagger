from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel


HIDE_DELAY_MS = 3000  # the bar fades after this long without input
_TRACK = QColor(255, 255, 255, 80)  # the whole length, dimmer than the elapsed part
_TRACK_HEIGHT = 3  # a thin strip along the bottom edge, clear of the text
_EDGE = QColor(0, 0, 0, 200)  # around the light text and filled track, so they read over white frames as over black
_EDGE_OFFSETS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
_GEOMETRY_EVENTS = (QEvent.Type.Show, QEvent.Type.Hide, QEvent.Type.Move, QEvent.Type.Resize)


class ProgressBar(QLabel):
    """A video's progress, shown only while the video surface it follows is shown."""

    # Class-level defaults: Qt still sends events to the bar while destroying its viewer, after Python's GC may have
    # emptied the instance's attributes while breaking a reference cycle.
    _playing = False
    _area = None  # (rect, clear_at_the_bottom) from the latest place
    _obstacles = ()

    def __init__(self, parent, hide_delay=HIDE_DELAY_MS):
        super().__init__(parent)
        self.setContentsMargins(8, 2, 8, 2 + _TRACK_HEIGHT)  # the text ends above the track
        self._ticker = QTimer(self, interval=250, timeout=self._tick)
        self._hide_timer = QTimer(self, interval=hide_delay, singleShot=True, timeout=self.hide)
        self.hide()

    def follow(self, surface):
        surface.installEventFilter(self)

    def avoid(self, *widgets):
        """Sit above these widgets (siblings, such as the tag prompt) whenever they are shown."""
        self._obstacles = widgets
        for widget in widgets:
            widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched in self._obstacles:
            if event.type() in _GEOMETRY_EVENTS and self._area:
                self.place(*self._area)
            return False
        if event.type() == QEvent.Type.Hide and watched.isHidden():  # the surface itself, not a hidden ancestor
            self._playing = False
            self.hide()
        return False

    def place(self, rect, clear_at_the_bottom):
        """Along the bottom of rect, its full width, above the strip kept clear for the status bar."""
        self._area = (rect, clear_at_the_bottom)
        bottom = rect.bottom() + 1 - clear_at_the_bottom
        for widget in self._obstacles:
            if not widget.isHidden():
                bottom = min(bottom, widget.geometry().top())
        height = self.sizeHint().height()
        self.setGeometry(rect.left(), bottom - height, rect.width(), height)

    def start(self, engine):
        self._engine = engine
        self._show_elapsed(0)
        self._playing = True
        self.wake()

    def stop(self):
        """Stop asking the player anything, before it shuts down."""
        self._playing = False
        self._ticker.stop()
        self.hide()

    def wake(self):
        """Show the bar for another hide delay, if a video is playing."""
        if not self._playing:
            return
        self.show()
        self._tick()
        self._ticker.start()
        self._hide_timer.start()

    def _tick(self):
        if not self.isVisible():  # hidden, or its viewer closed: mpv may be gone, so don't ask it
            self._ticker.stop()
            return
        if self._engine.time_pos is None:  # mpv has no position while a clip loads or stops
            return
        self._show_elapsed(self._engine.time_pos)

    def _show_elapsed(self, seconds):
        duration = self._engine.duration
        self._fraction = seconds / duration
        with_hours = duration >= 60 * 60
        speed = self._engine.speed
        shown_speed = "" if speed == 1 else f" · {speed:g}×"
        self.setText(f"{_clock(seconds, with_hours)} / {_clock(duration, with_hours)}{shown_speed}")

    def paintEvent(self, event):
        with QPainter(self) as painter:
            top = self.height() - _TRACK_HEIGHT
            painter.fillRect(0, top, self.width(), _TRACK_HEIGHT, _TRACK)
            filled = int(self.width() * self._fraction)
            painter.fillRect(0, top - 1, filled, 1, _EDGE)  # so the light line reads over a white frame too
            painter.fillRect(0, top, filled, _TRACK_HEIGHT, Qt.GlobalColor.white)
            self._draw_edged_text(painter)

    def _draw_edged_text(self, painter):
        """The text in white over a one-pixel dark edge, in place of the label's own plain drawing."""
        area, flags = self.contentsRect(), int(self.alignment())
        painter.setPen(_EDGE)
        for dx, dy in _EDGE_OFFSETS:
            painter.drawText(area.translated(dx, dy), flags, self.text())
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(area, flags, self.text())


def _clock(seconds, with_hours):
    minutes, seconds = divmod(round(seconds), 60)
    if with_hours:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"
