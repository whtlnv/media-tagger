from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class Viewer(QWidget):
    def __init__(self, folder):
        super().__init__()

    def paintEvent(self, event):
        QPainter(self).fillRect(self.rect(), QColor("red"))
