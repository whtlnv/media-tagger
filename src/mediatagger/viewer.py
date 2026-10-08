from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QWidget

from mediatagger.slideshow import Slideshow


class Viewer(QWidget):
    def __init__(self, folder):
        super().__init__()
        self.slideshow = Slideshow.open(folder)

    def paintEvent(self, event):
        QPainter(self).drawImage(self.rect(), QImage(str(self.slideshow.current)))
