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
        if is_video(self.slideshow.current):
            QOpenGLWidget(self)
            self.video_player = VideoPlayer(mpv.MPV(vo="null", ao="null"))
            self.video_player.show(self.slideshow.current)

    def paintEvent(self, event):
        QPainter(self).drawImage(self.rect(), QImage(str(self.slideshow.current)))
