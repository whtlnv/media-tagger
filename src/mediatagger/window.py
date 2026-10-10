from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from mediatagger.viewer import Viewer


class Window(QWidget):
    def __init__(self, path, player_options=None):
        super().__init__()
        stack = QStackedWidget(self)
        stack.addWidget(Viewer(path, player_options=player_options))
        QVBoxLayout(self).addWidget(stack)
