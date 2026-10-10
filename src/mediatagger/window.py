from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from mediatagger.grid import TILE_ROLE, Grid
from mediatagger.status_bar import StatusBar
from mediatagger.viewer import Viewer


class Window(QWidget):
    def __init__(self, path=None, player_options=None, **viewer_options):
        super().__init__()
        self.stack = QStackedWidget(self)
        self.viewer = Viewer(path, player_options=player_options, on_escape=self._escape, **viewer_options)
        self.stack.addWidget(self.viewer)
        self.status_bar = StatusBar(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)
        layout.addWidget(self.status_bar)

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

    def _show_tags_of(self, index):
        library = self.viewer.session.library
        if library:
            self.status_bar.show_tags(" ".join(library.tags(index.data(TILE_ROLE).path)))

    def _leave(self, folder):
        if self.viewer.session.is_mount_point(folder):
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
