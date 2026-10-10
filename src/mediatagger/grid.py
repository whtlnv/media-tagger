from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import QListView, QStyledItemDelegate

from mediatagger.folder import folder_entries, is_video

FOLDER_GLYPH = "📁"

IMAGE_GLYPH = "🖼"

VIDEO_GLYPH = "🎬"

VIDEO_BADGE = "▶"

TAG_BADGE = "🏷"


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
        entries = folder_entries(folder)
        names = [entry.name for entry in entries]
        self.setModel(QStringListModel(names, self))
        self.setItemDelegate(_TileDelegate(entries, library.tag_counts(folder) if library else {}, self))
        if at is not None:
            self.setCurrentIndex(self.model().index(names.index(at.name), 0))
