from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import QListView, QStyle, QStyledItemDelegate

from mediatagger.folder import is_video_name, subfolder_and_media_names
from mediatagger.thumbnail_scheduler import ThumbnailScheduler
from mediatagger.thumbnails import thumbnail_and_duration

FOLDER_GLYPH = "📁"

IMAGE_GLYPH = "🖼"

VIDEO_GLYPH = "🎬"

VIDEO_BADGE = "▶"

TAG_BADGE = "🏷"

TILE_SIZE = QSize(200, 200)

ZOOM_STEP = QSize(40, 40)

MAX_TILE_SIZE = QSize(400, 400)

MIN_TILE_SIZE = QSize(100, 100)

TILE_ROLE = Qt.ItemDataRole.UserRole


class _Kind(Enum):
    FOLDER = FOLDER_GLYPH
    IMAGE = IMAGE_GLYPH
    VIDEO = VIDEO_GLYPH


@dataclass
class _Tile:
    """Everything a tile paints, gathered when the folder is listed so painting never touches the disk.
    The thumbnail and a video's duration arrive later, from the thumbnail workers."""

    path: Path
    name: str
    kind: _Kind
    tag_count: int = 0
    thumbnail: object = None
    duration: float = None


def _tiles(folder, tag_counts):
    """Built from names: a folder of thousands of files must open fast on a Pi, and parsing a Path per file doesn't."""
    counts_by_name = {path.name: count for path, count in tag_counts.items()}
    subfolders, media = subfolder_and_media_names(folder)
    kinds = [_Kind.FOLDER] * len(subfolders) + [_Kind.VIDEO if is_video_name(name) else _Kind.IMAGE for name in media]
    return [_Tile(folder / name, name, kind, counts_by_name.get(name, 0)) for name, kind in zip(subfolders + media, kinds)]


def _receive(tile, generated):
    tile.thumbnail, tile.duration = generated


class _FolderModel(QAbstractListModel):
    def __init__(self, tiles, parent):
        super().__init__(parent)
        self.tiles = tiles

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.tiles)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        tile = self.tiles[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return tile.name
        if role == TILE_ROLE:
            return tile
        return None


class _TileDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return self.parent().gridSize()  # a tile fills its grid cell

    def paint(self, painter, option, index):
        tile = index.data(TILE_ROLE)
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect.adjusted(2, 2, -2, -2), option.palette.highlight())  # the grid cursor
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, tile.kind.value)
        name = painter.fontMetrics().elidedText(tile.name, Qt.TextElideMode.ElideRight, option.rect.width())
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, name)
        if tile.kind is _Kind.VIDEO:
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, VIDEO_BADGE)
        if tile.tag_count:
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, f"{TAG_BADGE}{tile.tag_count}")


class Grid(QListView):
    up = Signal()
    escaped = Signal()
    dropped = Signal(Path)

    def __init__(self, folder, at=None, library=None):
        super().__init__()
        self.folder = folder
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setGridSize(TILE_SIZE)
        self.setUniformItemSizes(True)  # lays out thousands of tiles without asking each one its size
        self.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        tiles = _tiles(folder, library.tag_counts(folder) if library else {})
        self.setModel(_FolderModel(tiles, self))
        self.setItemDelegate(_TileDelegate(self))
        self._generate_thumbnails(tiles)
        self.setAcceptDrops(True)
        if at is not None:
            names = [tile.name for tile in tiles]
            self.setCurrentIndex(self.model().index(names.index(at.name), 0))

    def _generate_thumbnails(self, tiles):
        by_path = {tile.path: tile for tile in tiles}
        self._thumbnails = ThumbnailScheduler(thumbnail_and_duration, parent=self)
        self._thumbnails.generated.connect(lambda path, generated: _receive(by_path[path], generated))
        paths = list(by_path)
        # Started once the grid is up: workers decoding from the first moment would slow opening a big folder.
        QTimer.singleShot(0, self, lambda: self._thumbnails.enter_folder(self._current_first(paths)))

    def _current_first(self, paths):
        current = self.currentIndex().data()
        return sorted(paths, key=lambda path: path.name != current)

    def keep_clear_at_the_bottom(self, height):
        """Room below the last row for what lies over the grid's bottom edge (the window's status bar)."""
        self.setViewportMargins(0, 0, 0, height)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Plus:
            self.setGridSize((self.gridSize() + ZOOM_STEP).boundedTo(MAX_TILE_SIZE))
            return
        if event.key() == Qt.Key.Key_Minus:
            self.setGridSize((self.gridSize() - ZOOM_STEP).expandedTo(MIN_TILE_SIZE))
            return
        if event.key() == Qt.Key.Key_Return:
            self.activated.emit(self.currentIndex())
            return
        if event.key() == Qt.Key.Key_Backspace:
            self.up.emit()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.escaped.emit()
            return
        if event.key() == Qt.Key.Key_F:
            if self.window().isFullScreen():
                self.window().showNormal()
            else:
                self.window().showFullScreen()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        self.dropped.emit(Path(event.mimeData().urls()[0].toLocalFile()))
