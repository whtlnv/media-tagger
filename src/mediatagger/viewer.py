import os
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QImageIOHandler, QImageReader, QPainter
from PySide6.QtWidgets import QFileDialog, QLabel, QWidget

from mediatagger.folder import is_video
from mediatagger.library import Library
from mediatagger.mpv_surface import MpvSurface
from mediatagger.slideshow import Slideshow
from mediatagger.video import VideoPlayer, new_engine

PLAYER_OPTIONS = {"vo": "libmpv"}
VIDEO_KEYS = {Qt.Key.Key_M: "m", Qt.Key.Key_P: "p", Qt.Key.Key_Up: "Up", Qt.Key.Key_Down: "Down", Qt.Key.Key_Return: "Enter"}
# Explicit colours: the desktop theme's default text colour may be black, which vanishes on a black background.
LABEL_STYLE = "color: white; background-color: rgba(0, 0, 0, 160); padding: 8px 12px; border-radius: 6px; font-size: 18px;"
CORNER_MARGIN = 16
SLIDESHOW_KEYS = {Qt.Key.Key_Left: "Left", Qt.Key.Key_Right: "Right", Qt.Key.Key_Space: "Space"}
UNSUPPORTED_TEXT = "Unsupported"
STATUS_BAR_HEIGHT = 32
NO_LIBRARY_TEXT = "No library open"
LIBRARY_TEXT = "Library: {}"
NO_LIBRARY_VIEWING_ONLY_TEXT = "No library — viewing only"
DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT = "{} has no tag library — viewing only"
CREATE_LIBRARY_QUESTION = "Create a tag library on {}?"
READ_ONLY_BANNER_TEXT = "This drive is read-only — tags can't be saved"


def fitted_rect(size, bounds):
    target = QRect(QPoint(), size.scaled(bounds.size(), Qt.AspectRatioMode.KeepAspectRatio))
    target.moveCenter(bounds.center())
    return target


def is_openable(path):
    """A file is opened with its folder, so the folder must be listable too."""
    if not os.access(path, os.R_OK):
        return False
    return not path.is_file() or os.access(path.parent, os.R_OK)


def decode_fitted(path, bounds):
    """Decode an image no larger than bounds, so a 12 MP photo is never fully decoded just to be shrunk."""
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    size = reader.size()
    if reader.transformation() & QImageIOHandler.Transformation.TransformationRotate90:
        bounds = bounds.transposed()
    if size.isValid() and (size.width() > bounds.width() or size.height() > bounds.height()):
        reader.setScaledSize(size.scaled(bounds, Qt.AspectRatioMode.KeepAspectRatio))
    return reader.read()


class Viewer(QWidget):
    def __init__(self, path=None, player_options=None, folder_picker=None, is_mount_point=os.path.ismount, ask_to_create_library=None):
        super().__init__()
        self.is_mount_point = is_mount_point
        self.ask_to_create_library = ask_to_create_library
        self.folder_picker = folder_picker or self._pick_folder
        self.slideshow = None
        self.video_player = VideoPlayer(new_engine(**{**PLAYER_OPTIONS, **(player_options or {})}))
        self.surface = None
        self._decoded_key = self._decoded = None
        self.info = QLabel(self)
        self.info.setStyleSheet(LABEL_STYLE)
        self.info.move(CORNER_MARGIN, CORNER_MARGIN)
        self.info.hide()
        self.placeholder = QLabel(UNSUPPORTED_TEXT, self)
        self.placeholder.setStyleSheet(LABEL_STYLE)
        self.status_bar = QWidget(self)
        self.library_label = QLabel(NO_LIBRARY_TEXT, self.status_bar)
        self.read_only_banner = QLabel(READ_ONLY_BANNER_TEXT, self)
        self.read_only_banner.hide()
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setAcceptDrops(True)
        if path is None:
            self.placeholder.setText("Drop a folder or file here, or press o to open")
            return
        self._open(path)

    def closeEvent(self, event):
        if self.surface:
            self.surface.release()
        if self.video_player.engine.handle is not None:  # a second close must not call into a destroyed mpv handle
            self.video_player.engine.terminate()
        super().closeEvent(event)

    def resizeEvent(self, event):
        if self.surface:
            self.surface.setGeometry(self.rect())
        self.status_bar.setGeometry(0, self.height() - STATUS_BAR_HEIGHT, self.width(), STATUS_BAR_HEIGHT)
        self._centre(self.placeholder)

    def _centre(self, label):
        label.adjustSize()
        frame = label.geometry()
        frame.moveCenter(self.rect().center())
        label.setGeometry(frame)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        if self.slideshow is None:
            return
        image = self._current_image()
        painter.drawImage(fitted_rect(image.size(), self.rect()), image)

    def dragEnterEvent(self, event):
        if any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        self._stop_video()
        self._open(Path(event.mimeData().urls()[0].toLocalFile()))

    def _stop_video(self):
        self.video_player.press("Right")  # leaving the current item is what stops its video

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:  # interim: quits until the grid (Phase 7) makes Esc "back to grid"
            self.close()
            return
        if event.key() == Qt.Key.Key_F:
            self._toggle_fullscreen()
            return
        if self.slideshow is None:
            if event.key() == Qt.Key.Key_O:
                self._open(self.folder_picker())
            return
        if event.key() == Qt.Key.Key_I:
            self.slideshow.press("i")
            self._show_info()
            return
        if event.key() in VIDEO_KEYS:
            self.video_player.press(VIDEO_KEYS[event.key()])
            return
        if event.key() not in SLIDESHOW_KEYS:
            return
        key = SLIDESHOW_KEYS[event.key()]
        self.slideshow.press(key)
        self.video_player.press(key)
        self._refresh()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _pick_folder(self):
        picker = QFileDialog(self)
        picker.setFileMode(QFileDialog.FileMode.Directory)
        if picker.exec():
            return Path(picker.selectedFiles()[0])

    def _open(self, path):
        if path is None:
            return
        if not is_openable(path):
            self._show_cant_open(path)
            return
        showing_info = self.slideshow is not None and self.slideshow.overlay
        try:
            self.slideshow = Slideshow.open(path)
        except OSError:
            self._show_cant_open(path)
            return
        if self.slideshow is None:
            self._show_message(f"No images or videos in {path.name}")
            return
        self.placeholder.setText(UNSUPPORTED_TEXT)
        self._open_library(path)
        if showing_info:
            self.slideshow.press("i")
        self._refresh()

    def _open_library(self, path):
        drive = next(folder for folder in (path, *path.parents) if self.is_mount_point(folder))
        if drive == Path("/"):
            self.library_label.setText(NO_LIBRARY_VIEWING_ONLY_TEXT)
            return
        if not (drive / ".mediatagger").exists():
            if not self.ask_to_create_library(CREATE_LIBRARY_QUESTION.format(drive.name)):
                self.library_label.setText(DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT.format(drive.name))
                return
            Library.create(drive)
        self.read_only_banner.setVisible(not os.access(drive, os.W_OK))
        self.library_label.setText(LIBRARY_TEXT.format(drive.name))

    def _show_cant_open(self, path):
        self.slideshow = None
        self._show_message(f"Can't open {path.name}")

    def _show_message(self, text):
        self.placeholder.setText(text)
        self._centre(self.placeholder)
        self.placeholder.show()
        self.info.hide()
        if self.surface:
            self.surface.hide()

    def _refresh(self):
        self._show_current()
        self._show_info()
        self.update()

    def _show_info(self):
        self.info.setText(self.slideshow.overlay or "")
        self.info.adjustSize()
        self.info.setVisible(bool(self.slideshow.overlay))

    def _current_image(self):
        """The current item decoded to fit the window: once per item and window size, not on every paint."""
        key = (self.slideshow.current, self.size())
        if self._decoded_key != key:
            self._decoded_key, self._decoded = key, decode_fitted(self.slideshow.current, self.size())
        return self._decoded

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
