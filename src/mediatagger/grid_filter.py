from PySide6.QtCore import QEvent, QObject, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPolygonF
from PySide6.QtWidgets import QToolButton

WITH_TAGS = "With tags"

NO_TAGS = "No tags"

MISSING_TAGS = "Missing tags"

BUTTON_SIZE = 40

BUTTON_INSET = 12  # from the corner of the tiles

OFF_BACKING = QColor(0, 0, 0, 150)  # the tiles under it read through


class GridFilter(QObject):
    """Which files the grids show: every one (no filter), or only those matching the one active filter. One per window,
    shared by every grid it opens, kept while the app runs."""

    changed = Signal()

    def __init__(self):
        super().__init__()
        self.active = None

    def choose(self, text):
        """Choosing the active filter again turns filtering off."""
        self.active = None if text == self.active else text
        self.changed.emit()

    def shows(self, tag_count, missing_roots):
        """Whether a file with this many own tags (what its tag badge counts) and missing roots is shown."""
        if self.active == WITH_TAGS:
            return tag_count > 0
        if self.active == NO_TAGS:
            return tag_count == 0
        if self.active == MISSING_TAGS:
            return missing_roots > 0
        return True


class FilterButton(QToolButton):
    """The round button floating over a grid's bottom-right corner, just inside its tiles (so above the status bar's
    clear margin and left of the scroll bar), that opens the filter menu."""

    def __init__(self, grid, grid_filter):
        super().__init__(grid)
        self._filter = grid_filter
        self.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        self.setCheckable(True)  # checked while a filter is on
        grid_filter.changed.connect(self._show_filter)
        self._show_filter()
        grid.viewport().installEventFilter(self)  # the tiles' area moves with resizes, margins and the scroll bar
        self._place()

    def _show_filter(self):
        self.setChecked(self._filter.active is not None)
        self.setToolTip(f"Showing: {self._filter.active}" if self._filter.active else "Filter files")

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize:
            self._place()
        return False

    def _place(self):
        tiles = self.parent().viewport().geometry()
        self.move(tiles.right() + 1 - BUTTON_INSET - self.width(), tiles.bottom() + 1 - BUTTON_INSET - self.height())
        self.raise_()

    def paintEvent(self, event):
        """A dark translucent disc with a white funnel on it, drawn rather than typed so no font can lack it."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.palette().highlight().color() if self.isChecked() else OFF_BACKING)
        painter.drawEllipse(self.rect())
        painter.setBrush(Qt.GlobalColor.white)
        size = self.width()
        funnel = [(0.3, 0.32), (0.7, 0.32), (0.55, 0.5), (0.55, 0.7), (0.45, 0.7), (0.45, 0.5)]
        painter.drawPolygon(QPolygonF([QPointF(x * size, y * size) for x, y in funnel]))
