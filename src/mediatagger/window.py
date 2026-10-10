from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from mediatagger.grid import Grid
from mediatagger.viewer import Viewer


class Window(QWidget):
    def __init__(self, path, player_options=None):
        super().__init__()
        self.stack = QStackedWidget(self)
        self.viewer = Viewer(path, player_options=player_options, on_escape=self._show_grid)
        self.stack.addWidget(self.viewer)
        QVBoxLayout(self).addWidget(self.stack)

    def _show_grid(self):
        self.viewer.stop_video()
        current = self.viewer.slideshow.current
        grid = Grid(current.parent, at=current)
        self.stack.addWidget(grid)
        self.stack.setCurrentWidget(grid)
