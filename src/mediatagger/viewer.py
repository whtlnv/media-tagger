import mpv
from PySide6.QtCore import Qt
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
        self.surface = None
        self._show_current()

    def paintEvent(self, event):
        QPainter(self).drawImage(self.rect(), QImage(str(self.slideshow.current)))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_M:
            self.video_player.press("m")
            return
        key = "Left" if event.key() == Qt.Key.Key_Left else "Space"
        self.slideshow.press(key)
        self.video_player.press(key)
        self._show_current()
        self.update()

    def _show_current(self):
        if is_video(self.slideshow.current):
            self.surface = self.surface or QOpenGLWidget(self)
            self.surface.show()
            self.video_player.show(self.slideshow.current)
        elif self.surface:
            self.surface.hide()
