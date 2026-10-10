from PySide6.QtCore import QSize, QStringListModel, Qt
from PySide6.QtWidgets import QListView, QStyledItemDelegate

from mediatagger.folder import folder_entries, is_video

FOLDER_GLYPH = "📁"

IMAGE_GLYPH = "🖼"

VIDEO_GLYPH = "🎬"

VIDEO_BADGE = "▶"

TAG_BADGE = "🏷"

TILE_SIZE = QSize(200, 200)

ZOOM_STEP = QSize(40, 40)


def _glyph(entry):
    if entry.is_dir():
        return FOLDER_GLYPH
    return VIDEO_GLYPH if is_video(entry) else IMAGE_GLYPH


class _TileDelegate(QStyledItemDelegate):
    def __init__(self, entries, tag_counts, parent):
        super().__init__(parent)
        self._entries = entries
        self._tag_counts = tag_counts

    def paint(self, painter, option, index):
        entry = self._entries[index.row()]
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, _glyph(entry))
        name = painter.fontMetrics().elidedText(entry.name, Qt.TextElideMode.ElideRight, option.rect.width())
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, name)
        if is_video(entry):
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, VIDEO_BADGE)
        if entry in self._tag_counts:
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, f"{TAG_BADGE}{self._tag_counts[entry]}")


class Grid(QListView):
    def __init__(self, folder, at=None, library=None):
        super().__init__()
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setGridSize(TILE_SIZE)
        entries = folder_entries(folder)
        names = [entry.name for entry in entries]
        self.setModel(QStringListModel(names, self))
        tag_counts = library.tag_counts(folder) if library else {}
        self.setItemDelegate(_TileDelegate(entries, tag_counts, self))
        if at is not None:
            self.setCurrentIndex(self.model().index(names.index(at.name), 0))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Plus:
            self.setGridSize(self.gridSize() + ZOOM_STEP)
            return
        if event.key() == Qt.Key.Key_Minus:
            self.setGridSize(self.gridSize() - ZOOM_STEP)
            return
        super().keyPressEvent(event)
