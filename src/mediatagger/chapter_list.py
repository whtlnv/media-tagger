from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QAbstractItemView, QListWidget

from mediatagger.video_controls import clock

_STYLE = (
    "QListWidget { color: white; background-color: rgba(0, 0, 0, 170); border: none; border-radius: 6px; font-size: 18px; padding: 8px; }"
    " QListWidget::item { padding: 4px 12px; border-radius: 4px; }"
    " QListWidget::item:selected { color: black; background-color: rgb(255, 210, 0); }"  # the highlight, in the ticks' colour
)
NO_CHAPTERS_TEXT = "No chapters"


def moment_line(moment):
    """`1:23 goal, people:ana`; `h:mm:ss` from an hour on."""
    return f"{clock(moment.seconds, with_hours=moment.seconds >= 60 * 60)} {', '.join(moment.tags)}"


class ChapterList(QListWidget):
    """A video's moments, one line each, centred over its parent. It never takes the focus or the mouse: the viewer
    hands it the keys it uses."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet(_STYLE)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        parent.installEventFilter(self)  # to stay centred as it resizes
        self.hide()

    def show_moments(self, moments):
        self.clear()
        self.addItems([moment_line(moment) for moment in moments] or [NO_CHAPTERS_TEXT])
        if moments:
            self.setCurrentRow(0)
        self._place()
        self.show()
        self.raise_()  # over the video surface

    def step(self, rows):
        """Moves the highlight by rows, stopping at the first and last lines."""
        if self.currentRow() >= 0:
            self.setCurrentRow(min(max(self.currentRow() + rows, 0), self.count() - 1))

    def eventFilter(self, watched, event):
        if watched is self.parent() and event.type() == QEvent.Type.Resize and self.isVisible():
            self._place()
        return False

    def _place(self):
        bounds = self.parent().rect()
        width = min(bounds.width() - 32, max(self.sizeHintForColumn(0), 200) + 2 * self.frameWidth() + 24)
        height = min(bounds.height() - 32, self.sizeHintForRow(0) * self.count() + 2 * self.frameWidth() + 24)
        self.resize(max(width, 0), max(height, 0))
        frame = self.geometry()
        frame.moveCenter(bounds.center())
        self.setGeometry(frame)
