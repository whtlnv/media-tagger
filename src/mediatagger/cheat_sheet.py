from PySide6.QtCore import QEvent, QRect, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLineEdit, QWidget

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

_TEXT_PIXEL_SIZE = 18
_TEXT = QColor(235, 235, 235)
_BACKING = QColor(0, 0, 0, 170)  # dark enough to read on, light enough to see the media through
_PADDING = 24
_KEY_GAP = 16


def draw_sheet(painter, rect, keys):
    """A panel centred in rect: each key right-aligned before its meaning, light text on a dark translucent backing."""
    painter.save()
    font = painter.font()
    font.setPixelSize(_TEXT_PIXEL_SIZE)
    painter.setFont(font)
    metrics = painter.fontMetrics()
    key_width = max(metrics.horizontalAdvance(key) for key, _ in keys)
    action_width = max(metrics.horizontalAdvance(action) for _, action in keys)
    line = metrics.height()
    panel = QRect(0, 0, key_width + _KEY_GAP + action_width + 2 * _PADDING, len(keys) * line + 2 * _PADDING)
    panel.moveCenter(rect.center())
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_BACKING)
    painter.drawRoundedRect(panel, _PADDING / 2, _PADDING / 2)
    painter.setPen(_TEXT)
    for number, (key, action) in enumerate(keys):
        top = panel.top() + _PADDING + number * line
        painter.drawText(QRect(panel.left() + _PADDING, top, key_width, line), Qt.AlignmentFlag.AlignRight, key)
        painter.drawText(QRect(panel.left() + _PADDING + key_width + _KEY_GAP, top, action_width, line), Qt.AlignmentFlag.AlignLeft, action)
    painter.restore()


class CheatSheet(QWidget):
    """The keys of the screen shown, in a panel over the whole of its parent, toggled by `h` on any widget it watches.
    It never takes the mouse or the keyboard focus: everything under it works as without it."""

    def __init__(self, parent=None, shown=False, on_toggle=lambda shown: None, keys=lambda: GRID_KEYS):
        super().__init__(parent)
        self.keys = keys
        self.on_toggle = on_toggle
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if parent is not None:
            parent.installEventFilter(self)  # to keep covering it as it resizes
            self.setGeometry(parent.rect())
        self.shown = shown
        self.setVisible(shown)

    def watch(self, widget):
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched is self.parent() and event.type() == QEvent.Type.Resize:
            self.setGeometry(watched.rect())
            return False
        if event.type() != QEvent.Type.KeyPress:
            return False
        if event.key() == Qt.Key.Key_H and not event.modifiers():
            self._show(not self.shown)
            return True
        typing = isinstance(watched.window().focusWidget(), QLineEdit)  # Esc there closes the tag prompt, as always
        if event.key() == Qt.Key.Key_Escape and self.shown and not typing:  # hides the sheet rather than quitting or going back
            self._show(False)
            return True
        return False

    def _show(self, shown):
        self.shown = shown
        self.setVisible(shown)
        self.raise_()
        self.on_toggle(shown)

    def paintEvent(self, event):
        painter = QPainter(self)
        draw_sheet(painter, self.rect(), self.keys())
