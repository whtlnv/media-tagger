from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from mediatagger.grid import TILE_ROLE, Grid
from mediatagger.viewer import Viewer


class Window(QWidget):
    def __init__(self, path=None, player_options=None, **viewer_options):
        super().__init__()
        self.stack = QStackedWidget(self)
        on_escape = self._show_grid if path else self.close
        self.viewer = Viewer(path, player_options=player_options, on_escape=on_escape, **viewer_options)
        self.stack.addWidget(self.viewer)
        QVBoxLayout(self).addWidget(self.stack)

    def _show_grid(self):
        self.viewer.stop_video()
        current = self.viewer.slideshow.current
        self._show(Grid(current.parent, at=current))

    def _show(self, grid):
        grid.activated.connect(self._show_viewer_at)
        self.stack.addWidget(grid)
        self.stack.setCurrentWidget(grid)

    def _show_viewer_at(self, index):
        path = index.data(TILE_ROLE).path
        if path.is_dir():
            grid = Grid(path)
            grid.setCurrentIndex(grid.model().index(0, 0))
            self._show(grid)
            return
        self.viewer.open(path)
        self.stack.setCurrentWidget(self.viewer)
