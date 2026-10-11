from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QListView, QStyle, QStyledItemDelegate

from mediatagger.folder import is_video_name, subfolder_and_media_names
from mediatagger.folder_thumbnails import FolderThumbnails
from mediatagger.thumbnail_cache import ThumbnailCache
from mediatagger.thumbnails import format_duration, thumbnail_and_duration

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

BADGE_PADDING = 4

BADGE_BACKING = QColor(0, 0, 0, 180)

HELD_THUMBNAILS = 500  # pictures kept in memory at once (about 240 MB), beyond those in view, which are always kept


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
    """Paints a tile from its _Tile alone: the picture (or a large type glyph) fills the tile above the filename, and
    the badges sit over the picture's corners on dark backings, legible over any picture."""

    def sizeHint(self, option, index):
        return self.parent().gridSize()  # a tile fills its grid cell

    def paint(self, painter, option, index):
        tile = index.data(TILE_ROLE)
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect.adjusted(2, 2, -2, -2), option.palette.highlight())  # the grid cursor
        picture_area = option.rect.adjusted(0, 0, 0, -painter.fontMetrics().height())  # leaves the filename's line free
        if tile.thumbnail is not None:
            picture = QRect(option.rect.topLeft(), tile.thumbnail.size().scaled(picture_area.size(), Qt.AspectRatioMode.KeepAspectRatio))
            picture.moveCenter(picture_area.center())
            painter.drawImage(picture, tile.thumbnail)
        else:
            _draw_glyph(painter, picture_area, tile.kind.value)
        name = painter.fontMetrics().elidedText(tile.name, Qt.TextElideMode.ElideRight, option.rect.width())
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, name)
        if tile.kind is _Kind.VIDEO:
            badge = VIDEO_BADGE if tile.duration is None else f"{VIDEO_BADGE} {format_duration(tile.duration)}"
            _draw_backed_badge(painter, picture_area, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, badge)
        if tile.tag_count:
            _draw_backed_badge(painter, option.rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, f"{TAG_BADGE}{tile.tag_count}")


def _draw_glyph(painter, area, glyph):
    """Large enough to read across the room: about a third of the picture area's height."""
    painter.save()
    font = painter.font()
    font.setPixelSize(max(12, area.height() // 3))
    painter.setFont(font)
    painter.drawText(area, Qt.AlignmentFlag.AlignCenter, glyph)
    painter.restore()


def _draw_backed_badge(painter, rect, flags, badge):
    """White text on a dark, rounded backing: reads over a white picture, a black one, and anything between."""
    painter.save()
    font = painter.font()
    font.setBold(True)
    painter.setFont(font)
    inside = rect.adjusted(2 * BADGE_PADDING, BADGE_PADDING, -2 * BADGE_PADDING, -BADGE_PADDING)  # off the tile's edges
    backing = painter.boundingRect(inside, flags, badge).adjusted(-BADGE_PADDING, 0, BADGE_PADDING, 0)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(BADGE_BACKING)
    painter.drawRoundedRect(backing, BADGE_PADDING, BADGE_PADDING)
    painter.setPen(Qt.GlobalColor.white)
    painter.drawText(inside, flags, badge)
    painter.restore()


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
        self._thumbnails = FolderThumbnails(list(rows), cache, self, generate=lambda path: thumbnail_and_duration(path))
        self._thumbnails.arrived.connect(lambda path, thumbnail, duration: self._show_thumbnail(tiles, rows[path], thumbnail, duration))
        self.thumbnail_progress = self._thumbnails.progress
        self._answered = OrderedDict()  # rows whose thumbnail (or lack of one) has arrived, least recently first
        self.verticalScrollBar().valueChanged.connect(self._request_visible)
        self._tiles = None  # set once generating has started, after the grid is first laid out and scrolled to its cursor
        # Started once the grid is up: workers decoding from the first moment would slow opening a big folder.
        QTimer.singleShot(0, self, lambda: self._start_generating(tiles))

    def _start_generating(self, tiles):
        self._tiles = tiles
        self._thumbnails.start()
        self._request_visible()

    def stop_generating_thumbnails(self):
        self._thumbnails.stop()

    def _show_thumbnail(self, tiles, row, thumbnail, duration):
        if row in self._answered and tiles[row].thumbnail is not None:
            return  # asked twice while on its way: the first answer is already shown
        tiles[row].thumbnail, tiles[row].duration = thumbnail, duration
        self._answered[row] = None
        self._answered.move_to_end(row)
        if len(self._answered) > HELD_THUMBNAILS:
            self._let_go_of_a_picture_out_of_view(tiles)
        index = self.model().index(row, 0)
        self.model().dataChanged.emit(index, index)

    def _let_go_of_a_picture_out_of_view(self, tiles):
        """The tile that got its picture longest ago and is out of view lets it go; back in view, it asks again."""
        viewport = self.viewport().rect()
        for row in self._answered:
            if not self.visualRect(self.model().index(row, 0)).intersects(viewport):
                del self._answered[row]
                tiles[row].thumbnail = None
                return

    def _request_visible(self):
        """The tiles in view, bottom-right first, and the cursor's tile last: the most recent request is generated
        first, so the cursor's tile comes first, then the top-left one. Only the rows from the first to the last
        visible tile are looked at, however big the folder; tiles already answered are not asked again."""
        tiles = getattr(self, "_tiles", None)  # not before generating has started
        if tiles is None:
            return
        viewport = self.viewport().rect()
        first = self.indexAt(viewport.topLeft())
        if not first.isValid():
            return
        last_row = first.row()
        while last_row + 1 < len(tiles) and self.visualRect(self.model().index(last_row + 1, 0)).intersects(viewport):
            last_row += 1
        current = self.currentIndex().row() if self.currentIndex().isValid() else None
        for row in [*range(last_row, first.row() - 1, -1), current]:  # the cursor's tile last, so generated first
            if row is not None and row not in self._answered:
                self._thumbnails.request(tiles[row].path)

    def updateGeometries(self):
        """Called once the tiles are laid out, and again whenever they move (resizing, zooming): what is in view changed."""
        super().updateGeometries()
        self._request_visible()

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
