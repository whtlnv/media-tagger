from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QLabel, QWidget

from mediatagger.folder import is_video
from mediatagger.slideshow import Slideshow
from mediatagger.video import VideoPlayer, new_engine

PLAYER_OPTIONS = {"vo": "libmpv"}
VIDEO_KEYS = {Qt.Key.Key_M: "m", Qt.Key.Key_P: "p", Qt.Key.Key_Up: "Up"}


def fitted_rect(size, bounds):
    target = QRect(QPoint(), size.scaled(bounds.size(), Qt.AspectRatioMode.KeepAspectRatio))
    target.moveCenter(bounds.center())
    return target


class Viewer(QWidget):
    def __init__(self, folder, player_options=None):
        super().__init__()
        self.slideshow = Slideshow.open(folder)
        self.video_player = VideoPlayer(new_engine(**{**PLAYER_OPTIONS, **(player_options or {})}))
        self.surface = None
        self.info = QLabel(self)
        self.info.hide()
        self.placeholder = QLabel("Unsupported", self)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self._show_current()

    def closeEvent(self, event):
        if self.video_player.engine.handle is not None:  # a second close must not call into a destroyed mpv handle
            self.video_player.engine.terminate()
        super().closeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        image = QImage(str(self.slideshow.current))
        painter.drawImage(fitted_rect(image.size(), self.rect()), image)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_I:
            self.slideshow.press("i")
            self._show_info()
            return
        if event.key() == Qt.Key.Key_F:
            self._toggle_fullscreen()
            return
        if event.key() in VIDEO_KEYS:
            self.video_player.press(VIDEO_KEYS[event.key()])
            return
        key = "Left" if event.key() == Qt.Key.Key_Left else "Space"
        self.slideshow.press(key)
        self.video_player.press(key)
        self._show_current()
        self._show_info()
        self.update()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _show_info(self):
        self.info.setText(self.slideshow.overlay or "")
        self.info.adjustSize()
        self.info.setVisible(bool(self.slideshow.overlay))

    def _show_current(self):
        self.placeholder.setVisible(QImage(str(self.slideshow.current)).isNull())
        if is_video(self.slideshow.current):
            self.surface = self.surface or QOpenGLWidget(self)
            self.surface.show()
            self.video_player.show(self.slideshow.current)
        elif self.surface:
            self.surface.hide()
