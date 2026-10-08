import mpv
from PySide6.QtGui import QImage, QPainter
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget

from mediatagger.folder import is_video
from mediatagger.slideshow import Slideshow
from mediatagger.video import VideoPlayer


class Viewer(QWidget):
    def __init__(self, folder):
        super().__init__()
        self.slideshow = Slideshow.open(folder)
        self.video_player = VideoPlayer(mpv.MPV(vo="libmpv"))
        if is_video(self.slideshow.current):
            self.surface = QOpenGLWidget(self)
            self.video_player.show(self.slideshow.current)

    def paintEvent(self, event):
        QPainter(self).drawImage(self.rect(), QImage(str(self.slideshow.current)))

    def keyPressEvent(self, event):
        self.slideshow.press("Space")
        self.video_player.press("Space")
        self.surface.hide()
        self.update()
