from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from mediatagger.drive_session import DriveSession
from mediatagger.grid import TILE_ROLE, Grid
from mediatagger.gui_thread_gc import collect_garbage_on_the_gui_thread
from mediatagger.status_bar import StatusBar
from mediatagger.viewer import Viewer


class Window(QWidget):
    """The app's one window: the folder grid and the viewer in a stack, over which lies the one status bar they share,
    reporting the one drive session they share."""

    def __init__(self, path=None, player_options=None, folder_picker=None, **session_options):
        super().__init__()
        collect_garbage_on_the_gui_thread()
        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.status_bar = StatusBar(self)
        self.session = DriveSession(self.status_bar, self, **session_options)
        self.viewer = Viewer(path, player_options=player_options, folder_picker=folder_picker, on_escape=self._escape, session=self.session)
        self.stack.addWidget(self.viewer)

    def resizeEvent(self, event):
        self.status_bar.place_along_the_bottom_of(self.rect())
        self.status_bar.raise_()

    def closeEvent(self, event):
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

    def _show(self, grid):
        grid.activated.connect(self._open_tile)
        grid.up.connect(lambda: self._leave(grid.folder))
        grid.escaped.connect(self.close)
        grid.dropped.connect(self._open)
        grid.selectionModel().currentChanged.connect(self._show_tags_of)
        for old in self.findChildren(Grid):
            old.deleteLater()
        self.stack.addWidget(grid)
        self.stack.setCurrentWidget(grid)
        self.status_bar.raise_()

    def _show_tags_of(self, index):
        library = self.session.library
        if library:
            self.status_bar.show_tags(" ".join(library.tags(index.data(TILE_ROLE).path)))

    def _leave(self, folder):
        if self.session.is_mount_point(folder):
            return
        self._show_parent_of(folder)

    def _show_parent_of(self, path):
        self._show(Grid(path.parent, at=path))

    def _open_tile(self, index):
        path = index.data(TILE_ROLE).path
        if path.is_dir():
            grid = Grid(path)
            grid.setCurrentIndex(grid.model().index(0, 0))
            self._show(grid)
            return
        self._open(path)

    def _open(self, path):
        self.viewer.open(path)
        self.stack.setCurrentWidget(self.viewer)
