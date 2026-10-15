from PySide6.QtCore import QEvent, QObject, QRect, Qt
from PySide6.QtGui import QColor

from mediatagger.status_bar import CORNER_MARGIN

GRID_KEYS = [
    ("arrows", "move"),
    ("Enter", "open"),
    ("Backspace", "up a folder"),
    ("/", "search"),
    ("t", "tag"),
    ("+ / -", "tile size"),
    ("Esc", "quit; in a search, back to the folder"),
    ("f", "fullscreen"),
    ("o", "open a folder"),
    ("h", "show / hide this list of keys"),
]

VIEWER_KEYS = [
    ("Space / →", "next"),
    ("←", "previous"),
    ("t", "tag"),
    ("i", "file name and position"),
    ("Esc", "back to the grid"),
    ("f", "fullscreen"),
    ("p / Enter", "play / pause"),
    ("↑ / ↓", "back / ahead 10 s"),
    ("0–9", "jump to 0 %–90 %"),
    ("m", "mute"),
    ("] / [", "faster / slower"),
    ("r", "turn 90°"),
    ("v", "show the progress bar"),
    ("o", "open a folder"),
    ("mouse wheel", "zoom in / out"),
    ("h", "show / hide this list of keys"),
]

LAUNCH_KEYS = [
    ("o", "open a folder"),
    ("f", "fullscreen"),
    ("Esc", "quit"),
    ("h", "show / hide this list of keys"),
]

TEXT_PIXEL_SIZE = 18
OPACITY = 0.3
_COLUMN_GAP = 48
_KEY_GAP = 16


class CheatSheet(QObject):
    """The list of keys drawn as a screen's background, toggled by `h` on any widget it watches."""

    def __init__(self, shown=False):
        super().__init__()
        self.shown = shown

    def watch(self, widget):
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_H and not event.modifiers():
            self.shown = not self.shown
            (watched.viewport() if hasattr(watched, "viewport") else watched).update()
            return True
        return False

    def paint(self, painter, rect, keys, colour):
        """The keys in columns from rect's top-left, keys right-aligned before their actions, in a faint colour."""
        if not self.shown:
            return
        painter.save()
        font = painter.font()
        font.setPixelSize(TEXT_PIXEL_SIZE)
        painter.setFont(font)
        colour = QColor(colour)
        colour.setAlphaF(OPACITY)
        painter.setPen(colour)
        metrics = painter.fontMetrics()
        key_width = max(metrics.horizontalAdvance(key) for key, _ in keys)
        action_width = max(metrics.horizontalAdvance(action) for _, action in keys)
        line = metrics.height()
        area = rect.adjusted(CORNER_MARGIN, CORNER_MARGIN, -CORNER_MARGIN, -CORNER_MARGIN)
        rows = max(1, area.height() // line)
        for number, (key, action) in enumerate(keys):
            left = area.left() + (number // rows) * (key_width + _KEY_GAP + action_width + _COLUMN_GAP)
            top = area.top() + (number % rows) * line
            painter.drawText(QRect(left, top, key_width, line), Qt.AlignmentFlag.AlignRight, key)
            painter.drawText(QRect(left + key_width + _KEY_GAP, top, action_width, line), Qt.AlignmentFlag.AlignLeft, action)
        painter.restore()
