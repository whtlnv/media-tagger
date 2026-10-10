from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import QListView, QStyledItemDelegate

from mediatagger.folder import folder_entries, is_video

FOLDER_GLYPH = "📁"

IMAGE_GLYPH = "🖼"

VIDEO_GLYPH = "🎬"

VIDEO_BADGE = "▶"


def _glyph(entry):
    if entry.is_dir():
        return FOLDER_GLYPH
    return VIDEO_GLYPH if is_video(entry) else IMAGE_GLYPH


class _GlyphDelegate(QStyledItemDelegate):
    def __init__(self, entries, parent):
        super().__init__(parent)
        self._entries = entries

    def paint(self, painter, option, index):
        entry = self._entries[index.row()]
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, _glyph(entry))
        if is_video(entry):
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, VIDEO_BADGE)


class Grid(QListView):
    def __init__(self, folder, at=None):
        super().__init__()
        entries = folder_entries(folder)
        names = [entry.name for entry in entries]
        self.setModel(QStringListModel(names, self))
        self.setItemDelegate(_GlyphDelegate(entries, self))
        if at is not None:
            self.setCurrentIndex(self.model().index(names.index(at.name), 0))
