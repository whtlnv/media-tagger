from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QListView, QStyle, QStyledItemDelegate

from mediatagger.drive_config import missing_roots
from mediatagger.folder import is_video_name, subfolder_and_media_names
from mediatagger.folder_thumbnails import FolderThumbnails
from mediatagger.grid_filter import FilterButton
from mediatagger.icons import Icon, draw_icon
from mediatagger.thumbnail_cache import ThumbnailCache
from mediatagger.thumbnails import format_duration, thumbnail_and_duration

FOLDER_GLYPH = Icon.FOLDER

FOLDER_BADGE = "📁"

IMAGE_GLYPH = Icon.PICTURE

VIDEO_GLYPH = "🎬"

MISSING_GLYPH = "❓"

VIDEO_BADGE = "▶"

TAG_BADGE = Icon.TAG

MISSING_ROOTS_BADGE = "✗"
MOMENTS_BADGE = Icon.STOPWATCH

TILE_SIZE = QSize(200, 200)

ZOOM_STEP = QSize(40, 40)

MAX_TILE_SIZE = QSize(400, 400)

MIN_TILE_SIZE = QSize(100, 100)

TILE_ROLE = Qt.ItemDataRole.UserRole

CURSOR_WIDTH = 4

TILE_MARGIN = 0.07  # of the cell's width, on every side

BADGE_PADDING = 4

BADGE_BACKING = QColor(0, 0, 0, 180)

HELD_THUMBNAILS = 500  # pictures kept in memory at once (about 240 MB), beyond those in view, which are always kept


class _Kind(Enum):
    FOLDER = FOLDER_GLYPH
    IMAGE = IMAGE_GLYPH
    VIDEO = VIDEO_GLYPH
    MISSING = MISSING_GLYPH


@dataclass
class _Tile:
    """Everything a tile paints, gathered when the folder is listed so painting never touches the disk.
    The thumbnail and a video's duration arrive later, from the thumbnail workers."""

    path: Path
    name: str
    kind: _Kind
    tag_count: int = 0
    missing_roots: int = 0  # of the drive's required roots, by the file's effective tags (inherited ones included)
    moments: int = 0  # a video's chapter moments
    thumbnail: object = None
    duration: float = None


def _tiles(folder):
    """Built from names: a folder of thousands of files must open fast on a Pi, and parsing a Path per file doesn't."""
    subfolders, media = subfolder_and_media_names(folder)
    kinds = [_Kind.FOLDER] * len(subfolders) + [_Kind.VIDEO if is_video_name(name) else _Kind.IMAGE for name in media]
    return [_Tile(folder / name, name, kind) for name, kind in zip(subfolders + media, kinds)]


def _own_tag_counts(tiles, folder, library, results):
    """Each tile's own-tag count, read in bulk: results by their full path, a folder's items by their name."""
    if results:
        counts = library.own_tag_counts()
        return [counts.get(str(tile.path), 0) for tile in tiles]
    counts = {path.name: count for path, count in library.tag_counts(folder).items()}
    return [counts.get(tile.name, 0) for tile in tiles]


def _moment_counts(tiles, folder, library, results):
    """Each tile's number of chapter moments, read in bulk like the tag counts."""
    if results:
        counts = library.all_moment_counts()
        return [counts.get(str(tile.path), 0) for tile in tiles]
    counts = {path.name: count for path, count in library.moment_counts(folder).items()}
    return [counts.get(tile.name, 0) for tile in tiles]


def _effective_tags(tiles, folder, library, results):
    """Each file tile's effective tags (its own and those it inherits), None for the others, from bulk reads and never
    one query per tile: a folder's files share what they inherit from it; results look their ancestors up among every
    tagged item. Worked out on names: hashing a Path per file is too slow for a folder of thousands on a Pi."""
    if results:
        tagged = {rel_path: own for rel_path, (_kind, own) in library.tagged_items().items()}
        root = f"{library.root}/"
        return [_with_ancestors_tags(str(tile.path).removeprefix(root), tagged) if _is_file(tile) else None for tile in tiles]
    shared = library.effective_tags(folder)
    shared = {*shared.own, *shared.inherited}
    own = library.own_tags_in(folder)
    return [own.get(tile.name, set()) | shared if _is_file(tile) else None for tile in tiles]


def _with_ancestors_tags(rel_path, tagged):
    parts = rel_path.split("/")
    return set().union(*(tagged.get("/".join(parts[:end]), ()) for end in range(1, len(parts) + 1)))


def _is_file(tile):
    return tile.kind in (_Kind.IMAGE, _Kind.VIDEO)


def _mark_missing_roots(tiles, effective_tags, roots):
    """Each file tile counts the required roots its effective tags lack; folders and missing results are never marked."""
    for tile, tags in zip(tiles, effective_tags):
        if tags is not None:
            tile.missing_roots = missing_roots(tags, roots)


def _result_kind(path):
    if not path.exists():
        return _Kind.MISSING
    if path.is_dir():
        return _Kind.FOLDER
    return _Kind.VIDEO if is_video_name(path.name) else _Kind.IMAGE


def _result_tiles(paths):
    return [_Tile(path, path.name, _result_kind(path)) for path in paths]


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
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        picture_area, name_band = _tile_layout(option.rect, painter.fontMetrics().height())
        shown = picture_area
        if tile.thumbnail is not None:
            shown = QRect(picture_area.topLeft(), tile.thumbnail.size().scaled(picture_area.size(), Qt.AspectRatioMode.KeepAspectRatio))
            shown.moveCenter(picture_area.center())
            painter.drawImage(shown, tile.thumbnail)
        else:
            _draw_glyph(painter, picture_area, tile.kind.value)
        if selected:  # the grid cursor: drawn over the picture, so it shows on any picture
            _draw_cursor(painter, shown, name_band, option.palette.highlight().color())
        name = painter.fontMetrics().elidedText(tile.name, Qt.TextElideMode.ElideRight, name_band.width())
        painter.save()
        if selected:
            painter.setPen(option.palette.highlightedText().color())
        painter.drawText(name_band, Qt.AlignmentFlag.AlignCenter, name)
        painter.restore()
        if tile.kind is _Kind.VIDEO:
            badge = VIDEO_BADGE if tile.duration is None else f"{VIDEO_BADGE} {format_duration(tile.duration)}"
            _draw_backed_badge(painter, picture_area, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, badge)
        top_right = picture_area  # the top-right badges read, left to right: missing roots, tags, moments
        if tile.moments:
            moments_badge = _draw_backed_badge(painter, top_right, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, str(tile.moments), MOMENTS_BADGE)
            top_right = top_right.adjusted(0, 0, moments_badge.left() - top_right.right(), 0)
        if tile.tag_count:
            tag_badge = _draw_backed_badge(painter, top_right, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, str(tile.tag_count), TAG_BADGE)
            top_right = top_right.adjusted(0, 0, tag_badge.left() - top_right.right(), 0)  # a badge's padding apart
        if tile.missing_roots:
            _draw_backed_badge(painter, top_right, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, f"{MISSING_ROOTS_BADGE}{tile.missing_roots}")
        if tile.kind is _Kind.FOLDER and tile.thumbnail is not None:  # its first image: marked so it can't pass for one
            _draw_backed_badge(painter, picture_area, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, FOLDER_BADGE)


def _draw_cursor(painter, picture, name_band, color):
    """A thick outline straddling the picture's edges, and the filename band filled."""
    painter.save()
    painter.fillRect(name_band, color)
    pen = QPen(color, CURSOR_WIDTH)
    pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRect(picture)
    painter.restore()


def _tile_layout(cell, line_height):
    """Where a tile's picture and filename go in its grid cell: inside a margin of about 7% of the cell, so neighbouring
    pictures never touch, the picture area above and the filename band along the bottom, apart from each other."""
    margin = max(4, round(cell.width() * TILE_MARGIN))
    inside = cell.adjusted(margin, margin, -margin, -margin)
    name_band = QRect(inside.left(), inside.bottom() + 1 - line_height, inside.width(), line_height)
    picture_area = inside.adjusted(0, 0, 0, -(line_height + margin // 2))
    return picture_area, name_band


def _draw_glyph(painter, area, glyph):
    """Large enough to read across the room: about a third of the picture area's height."""
    if isinstance(glyph, Icon):
        side = max(12, area.height() // 3)
        square = QRect(0, 0, side, side)
        square.moveCenter(area.center())
        draw_icon(painter, square, glyph, painter.pen().color())
        return
    painter.save()
    font = painter.font()
    font.setPixelSize(max(12, area.height() // 3))
    painter.setFont(font)
    painter.drawText(area, Qt.AlignmentFlag.AlignCenter, glyph)
    painter.restore()


def _draw_backed_badge(painter, rect, flags, badge, icon=None):
    """White text, after a white painted icon if given, on a dark, rounded backing: reads over a white picture, a black
    one, and anything between. Returns where the backing went."""
    painter.save()
    font = painter.font()
    font.setBold(True)
    painter.setFont(font)
    inside = rect.adjusted(2 * BADGE_PADDING, BADGE_PADDING, -2 * BADGE_PADDING, -BADGE_PADDING)  # off the tile's edges
    text_area = painter.boundingRect(inside, flags, badge)
    content = text_area
    if icon is not None:  # as tall as the text, just left of it
        side = painter.fontMetrics().height()
        icon_rect = QRect(text_area.left() - side // 6 - side, text_area.top(), side, side)
        content = text_area.united(icon_rect)
    backing = content.adjusted(-BADGE_PADDING, 0, BADGE_PADDING, 0)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(BADGE_BACKING)
    painter.drawRoundedRect(backing, BADGE_PADDING, BADGE_PADDING)
    if icon is not None:
        draw_icon(painter, icon_rect, icon, Qt.GlobalColor.white)
    painter.setPen(Qt.GlobalColor.white)
    painter.drawText(inside, flags, badge)
    painter.restore()
    return backing


class Grid(QListView):
    up = Signal()
    escaped = Signal()
    tag = Signal()
    rename_tag = Signal()
    search = Signal()
    pick_folder = Signal()
    dropped = Signal(Path)

    def __init__(self, folder, at=None, library=None, thumbnail_cache=None, paths=None, cheat_sheet=None, required_roots=(), grid_filter=None):
        super().__init__()
        self.folder = folder
        if cheat_sheet is not None:
            cheat_sheet.watch(self)  # `h` toggles it here, before the list's keyboard search could take it
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setGridSize(TILE_SIZE)
        self.setUniformItemSizes(True)  # lays out thousands of tiles without asking each one its size
        self.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        tiles = _result_tiles(paths) if paths is not None else _tiles(folder)
        self._required_roots, self._results = required_roots, paths is not None
        self.setModel(_FolderModel(tiles, self))
        self._filter = grid_filter
        if library:
            self.show_new_tags(library)
        else:
            self._apply_filter()
        if grid_filter is not None:
            grid_filter.changed.connect(self._apply_filter)
            FilterButton(self, grid_filter, offer_missing=bool(library and required_roots))  # only then are tiles marked
        self.setItemDelegate(_TileDelegate(self))
        self._generate_thumbnails(tiles, thumbnail_cache or ThumbnailCache(":memory:"))
        self.setAcceptDrops(True)
        if at is not None:
            names = [tile.name for tile in tiles]
            self.setCurrentIndex(self.model().index(names.index(at.name), 0))

    def _generate_thumbnails(self, tiles, cache):
        rows = {tile.path: row for row, tile in enumerate(tiles) if tile.kind is not _Kind.MISSING}
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
        in_view, row = [first.row()], first.row() + 1
        while row < len(tiles) and (self.isRowHidden(row) or self.visualRect(self.model().index(row, 0)).intersects(viewport)):
            if not self.isRowHidden(row):  # a hidden tile, filtered out, is stepped over and never asked for
                in_view.append(row)
            row += 1
        current = self.currentIndex().row() if self.currentIndex().isValid() else None
        for row in [*reversed(in_view), current]:  # the cursor's tile last, so generated first
            if row is not None and row not in self._answered and tiles[row].kind is not _Kind.MISSING:
                self._thumbnails.request(tiles[row].path)

    def updateGeometries(self):
        """Called once the tiles are laid out, and again whenever they move (resizing, zooming): what is in view changed."""
        super().updateGeometries()
        self._request_visible()

    def show_new_tags(self, library):
        """Every tile shows its own-tag count and missing roots afresh, and is filtered by them, read in bulk, without listing the folder again:
        tagging one item can change what others inherit."""
        tiles = self.model().tiles
        counts = _own_tag_counts(tiles, self.folder, library, self._results)
        for tile, count, moments in zip(tiles, counts, _moment_counts(tiles, self.folder, library, self._results)):
            tile.tag_count, tile.moments = count, moments
        if self._required_roots:
            _mark_missing_roots(tiles, _effective_tags(tiles, self.folder, library, self._results), self._required_roots)
        self._apply_filter()  # a file tagged so it no longer matches goes at once
        self.viewport().update()

    def _apply_filter(self):
        """Files the filter doesn't show are hidden in place; folder tiles and missing results always stay."""
        if self._filter is None:
            return
        for row, tile in enumerate(self.model().tiles):
            self.setRowHidden(row, _is_file(tile) and not self._filter.shows(tile.tag_count, tile.missing_roots))
        self.setCurrentIndex(self.currentIndex())  # off a tile just hidden

    def shown_files(self):
        """The files shown, in grid order: what a slideshow opened from here steps through."""
        return [tile.path for row, tile in enumerate(self.model().tiles) if _is_file(tile) and not self.isRowHidden(row)]

    def setCurrentIndex(self, index):
        """A hidden tile never takes the cursor: the nearest shown one does instead."""
        if index.isValid() and self.isRowHidden(index.row()):
            index = self._shown_near(index.row())
        super().setCurrentIndex(index)

    def _shown_near(self, row):
        """The first shown tile after row, else the last shown one before it, else none."""
        rows = [*range(row + 1, self.model().rowCount()), *range(row - 1, -1, -1)]
        return self.model().index(next((near for near in rows if not self.isRowHidden(near)), -1), 0)

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
            if self.currentIndex().isValid():  # an empty grid has no cursor, so nothing to open
                self.activated.emit(self.currentIndex())
            return
        if event.key() == Qt.Key.Key_Backspace:
            self.up.emit()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.escaped.emit()
            return
        if event.key() == Qt.Key.Key_T:
            self.tag.emit()
            return
        if event.key() == Qt.Key.Key_N:
            self.rename_tag.emit()
            return
        if event.key() == Qt.Key.Key_Slash:
            self.search.emit()
            return
        if event.key() == Qt.Key.Key_O:
            self.pick_folder.emit()
            return
        if event.key() == Qt.Key.Key_F:
            if self.window().isFullScreen():
                self.window().showNormal()
            else:
                self.window().showFullScreen()
            return
        if Qt.Key.Key_0 <= event.key() <= Qt.Key.Key_9:
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() and event.mimeData().urls()[0].isLocalFile():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.dropped.emit(Path(event.mimeData().urls()[0].toLocalFile()))
