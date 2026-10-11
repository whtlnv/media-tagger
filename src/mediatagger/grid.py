from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import QListView, QStyle, QStyledItemDelegate

from mediatagger.folder import is_video_name, subfolder_and_media_names
from mediatagger.thumbnail_cache import ThumbnailCache, generate_through_cache
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
    tile.thumbnail, tile.duration, _ = generated


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

    def __init__(self, folder, at=None, library=None, thumbnail_cache=None):
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
        self._generate_thumbnails(tiles, thumbnail_cache or ThumbnailCache(":memory:"))
        self.setAcceptDrops(True)
        if at is not None:
            names = [tile.name for tile in tiles]
            self.setCurrentIndex(self.model().index(names.index(at.name), 0))

    def _generate_thumbnails(self, tiles, cache):
        rows = {tile.path: row for row, tile in enumerate(tiles)}
        self._thumbnails = ThumbnailScheduler(lambda path: generate_through_cache(cache, thumbnail_and_duration, path), parent=self)
        self._thumbnails.generated.connect(lambda path, generated: self._show_thumbnail(tiles, rows[path], generated))
        paths = list(rows)
        self.verticalScrollBar().valueChanged.connect(lambda: self._request_visible(tiles))
        # Started once the grid is up: workers decoding from the first moment would slow opening a big folder.
        QTimer.singleShot(0, self, lambda: self._start_generating(tiles, paths))

    def _start_generating(self, tiles, paths):
        self._thumbnails.enter_folder(paths)
        self._request_visible(tiles)
        if self.currentIndex().isValid():
            self._thumbnails.request(tiles[self.currentIndex().row()].path)  # requested last, so generated first

    def stop_generating_thumbnails(self):
        self._thumbnails.shut_down()

    def _show_thumbnail(self, tiles, row, generated):
        _receive(tiles[row], generated)
        index = self.model().index(row, 0)
        self.model().dataChanged.emit(index, index)

    def _request_visible(self, tiles):
        """The tiles in view, bottom-right first: the most recent request is generated first, so the top-left
        tile comes first. Only the rows from the first to the last visible tile are looked at, however big the folder."""
        viewport = self.viewport().rect()
        first = self.indexAt(viewport.topLeft())
        if not first.isValid():
            return
        last_row = first.row()
        while last_row + 1 < len(tiles) and self.visualRect(self.model().index(last_row + 1, 0)).intersects(viewport):
            last_row += 1
        for row in range(last_row, first.row() - 1, -1):
            self._thumbnails.request(tiles[row].path)

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
