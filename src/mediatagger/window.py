from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication, QStackedWidget, QStyle, QVBoxLayout, QWidget

from mediatagger.cheat_sheet import GRID_KEYS, LAUNCH_KEYS, VIEWER_KEYS, CheatSheet
from mediatagger.drive_session import DriveSession
from mediatagger.folder_thumbnails import GENERATING_THUMBNAILS_TEXT, progress_text
from mediatagger.grid import TILE_ROLE, Grid
from mediatagger.grid_filter import GridFilter
from mediatagger.gui_thread_gc import collect_garbage_on_the_gui_thread
from mediatagger.search import search
from mediatagger.search_bar import SearchBar
from mediatagger.slideshow import Slideshow
from mediatagger.state import (remember, remember_cheat_sheet, remember_geometry, remember_search, remembered_cheat_sheet, remembered_folder,
    remembered_geometry, state_file)
from mediatagger.status_bar import StatusBar, overlay_label
from mediatagger.tag_prompt import TagPrompt
from mediatagger.viewer import Viewer


def _geometry_of(rect):
    return {"x": rect.x(), "y": rect.y(), "width": rect.width(), "height": rect.height()}


def _rect_of(geometry):
    return QRect(geometry["x"], geometry["y"], geometry["width"], geometry["height"])


class Window(QWidget):
    """The app's one window: the folder grid and the viewer in a stack, over which lies the one status bar they share,
    reporting the one drive session they share."""

    def __init__(self, path=None, player_options=None, folder_picker=None, home=None, **session_options):
        super().__init__()
        self._state_file = state_file(home or Path.home())
        remembered = remembered_folder(self._state_file) if path is None else None
        collect_garbage_on_the_gui_thread()
        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.search_bar = SearchBar(self._state_file, self)
        self.search_bar.submitted.connect(self.run_search)
        self.breadcrumb = overlay_label("", self)  # styled like the status bar, readable on a TV
        self.breadcrumb.setTextFormat(Qt.TextFormat.PlainText)  # a query is shown as typed, never as markup
        self.breadcrumb.hide()
        layout.addWidget(self.search_bar)
        layout.addWidget(self.breadcrumb)
        layout.addWidget(self.stack)
        self.status_bar = StatusBar(self)
        self.tag_prompt = TagPrompt(self, self.status_bar, on_close=self._show_saved_tags)
        self.session = DriveSession(self.status_bar, self, home=home or Path.home(), **session_options)
        self.viewer = Viewer(player_options=player_options, folder_picker=folder_picker, on_escape=self._escape, session=self.session,
            on_drop=self._record_state)
        self.stack.addWidget(self.viewer)
        self.cheat_sheet = CheatSheet(self, shown=remembered_cheat_sheet(self._state_file), on_toggle=self._record_cheat_sheet,
            keys=self._keys_on_screen)  # made after the stack and the status bar, so it lies over them
        self.cheat_sheet.watch(self.viewer)
        self.stack.currentChanged.connect(lambda: self.cheat_sheet.update())  # the keys of the screen now shown
        self._forwarding = False
        self._results = None
        self.grid_filter = GridFilter()  # shared by every grid, for as long as the app runs
        self.setAcceptDrops(True)
        geometry = remembered_geometry(self._state_file)
        if geometry:
            self.setGeometry(_rect_of(geometry))
        else:
            self._centre_on_the_screen()
        if path is not None:  # opened once the viewer is in place, so a question about the library is asked over it
            self._open(path.absolute())
        if remembered and remembered.exists():
            self.session.open_library(remembered)
            grid = self._grid_of(remembered)
            self._show(grid)
            grid.setCurrentIndex(grid.model().index(0, 0))

    def _centre_on_the_screen(self):
        available = self.screen().availableGeometry()
        self.setGeometry(QStyle.alignedRect(Qt.LayoutDirection.LeftToRight, Qt.AlignmentFlag.AlignCenter, available.size() * 0.8, available))

    def resizeEvent(self, event):
        self.status_bar.place_along_the_bottom_of(self.rect())
        self.status_bar.raise_()
        self.tag_prompt.place()

    def keyPressEvent(self, event):
        if self.tag_prompt.has_focus():
            if event.key() == Qt.Key.Key_Escape:
                self.tag_prompt.close()
            return
        self._forward_to_the_shown_page(event)

    def dragEnterEvent(self, event):
        if any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.viewer.stop_video()
        self._open(Path(event.mimeData().urls()[0].toLocalFile()))

    def _forward_to_the_shown_page(self, event):
        """Keys that reach the window itself belong to the page it shows. One the page ignores comes back up to the
        window, which then lets it go rather than forwarding it again."""
        if self._forwarding:
            return
        self._forwarding = True
        try:
            QApplication.sendEvent(self.stack.currentWidget(), event)
        finally:
            self._forwarding = False

    def closeEvent(self, event):
        self._record_geometry()
        for grid in self.findChildren(Grid):
            grid.stop_generating_thumbnails()
        self.viewer.close()  # shuts down its video player and backs up the session's library
        super().closeEvent(event)

    def _escape(self):
        if self.viewer.slideshow is None:
            self.close()
            return
        if self._results is not None:
            self._show_results()
            return
        self._show_grid()

    def _show_results(self):
        grid, paths = self._results
        self.viewer.stop_video()
        grid.setCurrentIndex(grid.model().index(paths.index(self.viewer.slideshow.current), 0))
        grid.show_new_tags(self.session.library)  # files tagged in the slideshow
        self._return_to(grid)

    def _show_grid(self):
        self.viewer.stop_video()
        self._show_parent_of(self.viewer.slideshow.current)

    def _grid_of(self, folder, at=None):
        return Grid(folder, at=at, library=self.session.library, thumbnail_cache=self.session.thumbnail_cache(), cheat_sheet=self.cheat_sheet,
            required_roots=self.session.required_roots, grid_filter=self.grid_filter)

    def _show(self, grid):
        grid.activated.connect(self._open_tile)
        grid.up.connect(lambda: self._leave(grid.folder))
        grid.escaped.connect(self.close)
        grid.dropped.connect(self._open)
        self._connect_tags_search_and_progress_of(grid)
        for old in self.findChildren(Grid):
            self._stop_thumbnails_of(old)
            old.deleteLater()
        grid.keep_clear_at_the_bottom(self.status_bar.sizeHint().height())
        self.stack.addWidget(grid)
        self.stack.setCurrentWidget(grid)
        self.status_bar.raise_()
        self._record_state(grid.folder)

    def _connect_tags_search_and_progress_of(self, grid):
        """What a folder's grid and a results grid both do: tag the cursor's item, search again, pick a folder, show its
        tags, and count its thumbnails."""
        grid.tag.connect(lambda: self._tag(grid.currentIndex()))
        grid.search.connect(self._open_search_bar)
        grid.pick_folder.connect(self._pick_folder)
        grid.selectionModel().currentChanged.connect(self._show_tags_of)
        grid.thumbnail_progress.connect(self._show_thumbnail_progress)

    def _stop_thumbnails_of(self, grid):
        """A folder left behind stops generating, and its unfinished count leaves the status bar."""
        grid.stop_generating_thumbnails()
        self.status_bar.clear_background(GENERATING_THUMBNAILS_TEXT.split("{")[0])

    def _show_thumbnail_progress(self, done, total):
        self.status_bar.show_background(progress_text(done, total), finished=done == total)

    def _record_state(self, folder):
        if self._may_write_state():
            remember(self._state_file, folder, self.session.drive)

    def _keys_on_screen(self):
        if self.stack.currentWidget() is not self.viewer:
            return GRID_KEYS
        return LAUNCH_KEYS if self.viewer.slideshow is None else VIEWER_KEYS

    def _record_cheat_sheet(self, shown):
        if self._may_write_state():
            remember_cheat_sheet(self._state_file, shown)

    def _record_geometry(self):
        """The normal size and position, also when fullscreen, so the next launch opens as a normal window there."""
        if not self.isVisible() or not self._may_write_state():
            return
        frame = self.normalGeometry() if self.isFullScreen() else self.geometry()
        remember_geometry(self._state_file, _geometry_of(frame))

    def _open_search_bar(self):
        if not self.session.library:
            return
        self.search_bar.open()

    def run_search(self, query):
        self.search_bar.hide()
        if not query.strip():
            self.stack.currentWidget().setFocus()
            return
        if self._may_write_state():
            remember_search(self._state_file, query)
        shown = self.stack.currentWidget()
        searched_from = getattr(shown, "searched_from", shown)  # searching again from results still returns to the folder
        if shown is not searched_from:
            self._drop_results(shown)
        paths = search(self.session.library, query)
        grid = Grid(self.session.drive, library=self.session.library, thumbnail_cache=self.session.thumbnail_cache(), paths=paths,
            cheat_sheet=self.cheat_sheet, required_roots=self.session.required_roots)
        grid.searched_from = searched_from
        grid.activated.connect(lambda index: self._open_result(index, paths, grid))
        grid.escaped.connect(lambda: self._end_search(searched_from))
        self._connect_tags_search_and_progress_of(grid)
        self.stack.addWidget(grid)
        self.stack.setCurrentWidget(grid)
        self.breadcrumb.setText(f"Search: {query}")
        self.breadcrumb.show()
        grid.setCurrentIndex(grid.model().index(0, 0))
        self._show_current_tags()  # no results: no cursor, so the last item's tags go
        grid.setFocus()

    def _end_search(self, searched_from):
        self.breadcrumb.hide()
        self._results = None
        results = self.stack.currentWidget()
        self._return_to(searched_from)
        self._drop_results(results)

    def _drop_results(self, results):
        self._stop_thumbnails_of(results)
        self.stack.removeWidget(results)
        results.deleteLater()

    def _return_to(self, grid):
        self.stack.setCurrentWidget(grid)
        grid.setFocus()

    def _may_write_state(self):
        return not (self._is_on_the_apps_own_drive(self._state_file) or self._is_on_the_drive_being_viewed(self._state_file))

    def _is_on_the_apps_own_drive(self, path):
        """The system disk is the home folder's own disk, so only an app drive other than `/` is kept clear."""
        app_drive = self.session.app_drive()
        return app_drive is not None and app_drive in path.parents

    def _is_on_the_drive_being_viewed(self, path):
        return self.session.drive in path.parents

    def _show_tags_of(self, index):
        if not index.isValid():
            self.status_bar.show_tags("")
            return
        library = self.session.library
        if not library:
            return
        tags = library.effective_tags(index.data(TILE_ROLE).path)
        self.status_bar.show_tags(" ".join(tags.own), " ".join(tags.inherited))

    def _show_current_tags(self):
        self._show_tags_of(self.stack.currentWidget().currentIndex())

    def _tag(self, index):
        if not index.isValid():
            return
        if not self.session.tags_can_be_saved():
            self.status_bar.flash_cant_save()
            return
        self.tag_prompt.open(self.session.library, index.data(TILE_ROLE).path)

    def _show_saved_tags(self, library, path):
        grid = self.stack.currentWidget()
        grid.show_new_tags(library)
        self._show_current_tags()

    def _leave(self, folder):
        if self.session.is_mount_point(folder):
            return
        self._show_parent_of(folder)

    def _show_parent_of(self, path):
        self._show(self._grid_of(path.parent, at=path))
        self._show_current_tags()

    def _open_tile(self, index):
        path = index.data(TILE_ROLE).path
        if path.is_dir():
            grid = self._grid_of(path)
            grid.setCurrentIndex(grid.model().index(0, 0))
            self._show(grid)
            self._show_current_tags()
            return
        self._open(path)

    def _open_result(self, index, paths, grid):
        if not index.data(TILE_ROLE).path.exists():
            return
        if index.data(TILE_ROLE).path.is_dir():
            self.breadcrumb.hide()
            self._results = None
            self._open_tile(index)
            return
        self._results = (grid, paths)
        self._open_tile(index)
        files = [path for path in paths if path.is_file()]
        self.viewer.slideshow = Slideshow(files, files.index(index.data(TILE_ROLE).path))

    def _pick_folder(self):
        folder = self.viewer.folder_picker()
        if folder:
            self._open(folder)

    def _open(self, path):
        if isinstance(self.stack.currentWidget(), Grid):  # a tile's Enter, a drop onto the grid, or a folder picked from it
            self._stop_thumbnails_of(self.stack.currentWidget())
        self.viewer.open(path)
        self.stack.setCurrentWidget(self.viewer)
        self.status_bar.show_tags("")
        if self.viewer.slideshow is not None:
            self._record_state(self.viewer.slideshow.current.parent)
