from pathlib import Path

from PySide6.QtCore import QEvent, QRect, Qt
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QStackedWidget, QStyle, QVBoxLayout, QWidget

from mediatagger.drive_session import DriveSession
from mediatagger.folder_thumbnails import GENERATING_THUMBNAILS_TEXT, progress_text
from mediatagger.grid import TILE_ROLE, Grid
from mediatagger.gui_thread_gc import collect_garbage_on_the_gui_thread
from mediatagger.search import search
from mediatagger.state import remember, remember_geometry, remembered_folder, remembered_geometry, state_file
from mediatagger.status_bar import StatusBar
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
        self.search_bar = QLineEdit(self)
        self.search_bar.hide()
        self.search_bar.installEventFilter(self)
        self.breadcrumb = QLabel(self)
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
        self._forwarding = False
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

    def eventFilter(self, watched, event):
        """Enter in the search bar runs the search and stops there, rather than going on to the page shown below it."""
        if watched is self.search_bar and event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Return:
            self.run_search(self.search_bar.text())
            return True
        if watched is self.search_bar and event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            self.run_search("")
            return True
        return super().eventFilter(watched, event)

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
        self.viewer.close()  # shuts down its video player and backs up the session's library
        super().closeEvent(event)

    def _escape(self):
        if self.viewer.slideshow is None:
            self.close()
            return
        self._show_grid()

    def _show_grid(self):
        self.viewer.stop_video()
        self._show_parent_of(self.viewer.slideshow.current)

    def _grid_of(self, folder, at=None):
        return Grid(folder, at=at, library=self.session.library, thumbnail_cache=self.session.thumbnail_cache())

    def _show(self, grid):
        grid.activated.connect(self._open_tile)
        grid.up.connect(lambda: self._leave(grid.folder))
        grid.escaped.connect(self.close)
        grid.tag.connect(lambda: self._tag(grid.currentIndex()))
        grid.search.connect(self._open_search_bar)
        grid.dropped.connect(self._open)
        grid.selectionModel().currentChanged.connect(self._show_tags_of)
        grid.thumbnail_progress.connect(self._show_thumbnail_progress)
        for old in self.findChildren(Grid):
            self._stop_thumbnails_of(old)
            old.deleteLater()
        grid.keep_clear_at_the_bottom(self.status_bar.sizeHint().height())
        self.stack.addWidget(grid)
        self.stack.setCurrentWidget(grid)
        self.status_bar.raise_()
        self._record_state(grid.folder)

    def _stop_thumbnails_of(self, grid):
        """A folder left behind stops generating, and its unfinished count leaves the status bar."""
        grid.stop_generating_thumbnails()
        self.status_bar.clear_background(GENERATING_THUMBNAILS_TEXT.split("{")[0])

    def _show_thumbnail_progress(self, done, total):
        self.status_bar.show_background(progress_text(done, total), finished=done == total)

    def _record_state(self, folder):
        if self._may_write_state():
            remember(self._state_file, folder, self.session.drive)

    def _record_geometry(self):
        """The normal size and position, also when fullscreen, so the next launch opens as a normal window there."""
        if not self.isVisible() or not self._may_write_state():
            return
        frame = self.normalGeometry() if self.isFullScreen() else self.geometry()
        remember_geometry(self._state_file, _geometry_of(frame))

    def _open_search_bar(self):
        if not self.session.library:
            return
        self.search_bar.show()
        self.search_bar.setFocus()

    def run_search(self, query):
        self.search_bar.hide()
        if not query.strip():
            self.stack.currentWidget().setFocus()
            return
        grid = Grid(self.session.drive, paths=search(self.session.library, query))
        self.stack.addWidget(grid)
        self.stack.setCurrentWidget(grid)
        self.breadcrumb.setText(f"Search: {query}")
        self.breadcrumb.show()
        grid.setCurrentIndex(grid.model().index(0, 0))
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
        grid.show_tag_count(len(library.tags(path)))
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

    def _open(self, path):
        if isinstance(self.stack.currentWidget(), Grid):  # a tile's Enter, or a drop onto the grid
            self._stop_thumbnails_of(self.stack.currentWidget())
        self.viewer.open(path)
        self.stack.setCurrentWidget(self.viewer)
        self.status_bar.show_tags("")
        if self.viewer.slideshow is not None:
            self._record_state(self.viewer.slideshow.current.parent)
