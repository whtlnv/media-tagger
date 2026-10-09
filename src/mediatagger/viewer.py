from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QLabel, QWidget

from mediatagger.folder import is_video
from mediatagger.mpv_surface import MpvSurface
from mediatagger.slideshow import Slideshow
from mediatagger.video import VideoPlayer, new_engine

PLAYER_OPTIONS = {"vo": "libmpv"}
VIDEO_KEYS = {Qt.Key.Key_M: "m", Qt.Key.Key_P: "p", Qt.Key.Key_Up: "Up", Qt.Key.Key_Down: "Down", Qt.Key.Key_Return: "Enter"}
# Explicit colours: the desktop theme's default text colour may be black, which vanishes on a black background.
LABEL_STYLE = "color: white; background-color: rgba(0, 0, 0, 160); padding: 8px 12px; border-radius: 6px; font-size: 18px;"
CORNER_MARGIN = 16
SLIDESHOW_KEYS = {Qt.Key.Key_Left: "Left", Qt.Key.Key_Right: "Right", Qt.Key.Key_Space: "Space"}


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
        self.info.setStyleSheet(LABEL_STYLE)
        self.info.move(CORNER_MARGIN, CORNER_MARGIN)
        self.info.hide()
        self.placeholder = QLabel("Unsupported", self)
        self.placeholder.setStyleSheet(LABEL_STYLE)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self._show_current()

    def closeEvent(self, event):
        if self.surface:
            self.surface.release()
        if self.video_player.engine.handle is not None:  # a second close must not call into a destroyed mpv handle
            self.video_player.engine.terminate()
        super().closeEvent(event)

    def resizeEvent(self, event):
        if self.surface:
            self.surface.setGeometry(self.rect())
        self._centre(self.placeholder)

    def _centre(self, label):
        label.adjustSize()
        frame = label.geometry()
        frame.moveCenter(self.rect().center())
        label.setGeometry(frame)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        image = self._current_image()
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
        if event.key() not in SLIDESHOW_KEYS:
            return
        key = SLIDESHOW_KEYS[event.key()]
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

    def _current_image(self):
        return QImage(str(self.slideshow.current))

    def _play(self, clip):
        if not self.video_player.show(clip):
            self.surface.hide()
            self.placeholder.show()

    def _show_current(self):
        video = is_video(self.slideshow.current)
        self.placeholder.setVisible(not video and self._current_image().isNull())
        if video:
            self.surface = self.surface or MpvSurface(self.video_player.engine, self)
            self.surface.setGeometry(self.rect())
            self.surface.show()
            self.info.raise_()
            self.surface.when_ready(lambda clip=self.slideshow.current: self._play(clip))
        elif self.surface:
            self.surface.cancel_pending()
            self.surface.hide()
