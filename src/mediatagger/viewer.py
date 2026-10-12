import os
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QFileDialog, QWidget

from mediatagger.drive_session import DriveSession
from mediatagger.folder import is_video
from mediatagger.gui_thread_gc import collect_garbage_on_the_gui_thread
from mediatagger.image_fit import decode_fitted, fitted_rect
from mediatagger.mpv_surface import MpvSurface
from mediatagger.status_bar import CORNER_MARGIN, StatusBar, TagOverlay, overlay_label
from mediatagger.slideshow import Slideshow
from mediatagger.tag_prompt import TagPrompt
from mediatagger.video import VideoPlayer, new_engine
from mediatagger.video_controls import ProgressBar

_PLAYER_OPTIONS = {"vo": "libmpv", "vd_lavc_dr": "no"}  # mpv_surface hands mpv no GL fences, which direct rendering needs
_VIDEO_KEYS = {Qt.Key.Key_M: "m", Qt.Key.Key_P: "p", Qt.Key.Key_Up: "Up", Qt.Key.Key_Down: "Down", Qt.Key.Key_Return: "Enter"}
_VIDEO_KEYS |= {Qt.Key.Key_0 + digit: str(digit) for digit in range(10)}
_SLIDESHOW_KEYS = {Qt.Key.Key_Left: "Left", Qt.Key.Key_Right: "Right", Qt.Key.Key_Space: "Space"}
UNSUPPORTED_TEXT = "Unsupported"
READ_ONLY_BANNER_TEXT = "This drive is read-only — tags can't be saved"


def _is_openable(path):
    """A file is opened with its folder, so the folder must be listable too."""
    if not os.access(path, os.R_OK):
        return False
    return not path.is_file() or os.access(path.parent, os.R_OK)


class Viewer(QWidget):
    def __init__(self, path=None, player_options=None, folder_picker=None, on_escape=None, session=None, on_drop=lambda path: None,
        **session_options,
    ):
        """A viewer on its own makes its own status bar and drive session; inside a window it is handed the window's."""
        super().__init__()
        self.on_escape = on_escape or self.close
        self.on_drop = on_drop
        collect_garbage_on_the_gui_thread()
        if session is None:
            session = DriveSession(StatusBar(self), self, **session_options)
        self.session = session
        self.status_bar = session.status_bar
        self.folder_picker = folder_picker or self._pick_folder
        self.slideshow = None
        self.video_player = VideoPlayer(new_engine(**{**_PLAYER_OPTIONS, **(player_options or {})}))
        self.surface = None
        self._decoded_key = self._decoded = None
        self.tag_prompt = TagPrompt(self, self.status_bar, on_close=self._show_tag_overlay)
        self.tag_overlay = TagOverlay(self)
        self.info = overlay_label("", self)
        self.info.move(CORNER_MARGIN, CORNER_MARGIN)
        self.info.hide()
        self.placeholder = overlay_label(UNSUPPORTED_TEXT, self)
        self.read_only_banner = overlay_label(READ_ONLY_BANNER_TEXT, self)
        self.read_only_banner.hide()
        self.progress_bar = ProgressBar(self)
        self.progress_bar.avoid(self.tag_prompt.input, self.tag_prompt.shown_tags)
        self.setAcceptDrops(True)
        if path is None:
            self.placeholder.setText("Drop a folder or file here, or press o to open")
            return
        self.open(path)

    def closeEvent(self, event):
        self.progress_bar.stop()  # its next tick must not read a terminated mpv
        if self.surface:
            self.surface.release()
        if self.video_player.engine.handle is not None:  # a second close must not call into a destroyed mpv handle
            self.video_player.engine.terminate()
        self.session.close()
        super().closeEvent(event)

    def resizeEvent(self, event):
        if self.surface:
            self.surface.setGeometry(self.rect())
        if self.status_bar.parent() is self:
            self.status_bar.place_along_the_bottom_of(self.rect())
        self.progress_bar.place(self.rect(), clear_at_the_bottom=self.status_bar.sizeHint().height())
        self._centre(self.placeholder)
        self._pin_top_centre(self.read_only_banner)
        self.tag_overlay.pin(self._pin_top_right)
        self.tag_prompt.place()

    def _centre(self, label):
        label.adjustSize()
        frame = label.geometry()
        frame.moveCenter(self.rect().center())
        label.setGeometry(frame)

    def _pin_top_centre(self, label):
        frame = label.geometry()
        frame.moveCenter(self.rect().center())
        frame.moveTop(CORNER_MARGIN)
        label.setGeometry(frame)

    def _pin_top_right(self, label):
        frame = label.geometry()
        top = CORNER_MARGIN
        if not self.read_only_banner.isHidden():
            top = self.read_only_banner.geometry().bottom() + CORNER_MARGIN // 2
        frame.moveTopRight(QPoint(self.rect().right() - CORNER_MARGIN, top))
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
        self.stop_video()
        path = Path(event.mimeData().urls()[0].toLocalFile())
        self.open(path)
        self.on_drop(path)

    def stop_video(self):
        self.video_player.press("Right")  # leaving the current item is what stops its video

    def keyPressEvent(self, event):
        self.progress_bar.wake()
        if event.key() == Qt.Key.Key_Escape and self.tag_prompt.has_focus():
            self.tag_prompt.close()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.on_escape()
            return
        if event.key() == Qt.Key.Key_F:
            self._toggle_fullscreen()
            return
        if self.slideshow is None:
            if event.key() == Qt.Key.Key_O:
                self.open(self.folder_picker())
            return
        if event.key() == Qt.Key.Key_I:
            self.slideshow.press("i")
            self._show_info()
            return
        if event.key() == Qt.Key.Key_T:
            if self.session.tags_can_be_saved():
                self.tag_overlay.hide()
                self.tag_prompt.open(self.session.library, self.slideshow.current)
            else:
                self.status_bar.flash_cant_save()
            return
        if self.tag_prompt.has_focus():
            return  # keys the open tag prompt ignores must not reach the slideshow or video
        if event.key() in _VIDEO_KEYS:
            self.video_player.press(_VIDEO_KEYS[event.key()])
            self.progress_bar.wake()
            return
        if event.key() not in _SLIDESHOW_KEYS:
            return
        key = _SLIDESHOW_KEYS[event.key()]
        self.slideshow.press(key)
        self.video_player.press(key)
        self._refresh()
        self._show_current_tags()

    def _show_current_tags(self):
        if self.session.library:
            self._show_tag_overlay(self.session.library, self.slideshow.current)

    def _show_tag_overlay(self, library, path):
        self.tag_overlay.show(library.effective_tags(path))
        self.tag_overlay.pin(self._pin_top_right)

    def _toggle_fullscreen(self):
        window = self.window()  # the app's window when inside it, else this viewer
        if window.isFullScreen():
            window.showNormal()
        else:
            window.showFullScreen()

    def _pick_folder(self):
        picker = QFileDialog(self)
        picker.setFileMode(QFileDialog.FileMode.Directory)
        if picker.exec():
            return Path(picker.selectedFiles()[0])

    def open(self, path):
        if path is None:
            return
        if self.tag_prompt.is_open():  # whatever opens next, the prompt must not go on targeting the previous item
            self.tag_prompt.close()
        if not _is_openable(path):
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
        if showing_info:
            self.slideshow.press("i")
        self._refresh()
        self.session.open_library(path)  # after the first item is shown, so a question about the library is asked over it
        self.read_only_banner.setVisible(self.session.read_only)
        self._show_current_tags()

    def _show_cant_open(self, path):
        self.slideshow = None
        self._show_message(f"Can't open {path.name}")

    def _show_message(self, text):
        self.placeholder.setText(text)
        self._centre(self.placeholder)
        self.placeholder.show()
        self.info.hide()
        self._hide_video()

    def _hide_video(self):
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
            self._hide_video()
            self.placeholder.show()
            return
        self.progress_bar.start(self.video_player.engine)

    def _show_current(self):
        video = is_video(self.slideshow.current)
        self.placeholder.setVisible(not video and self._current_image().isNull())
        if video:
            if self.surface is None:
                self.surface = MpvSurface(self.video_player.engine, self)
                self.progress_bar.follow(self.surface)
            self.surface.setGeometry(self.rect())
            self.surface.show()
            for overlay in (self.info, self.status_bar, self.read_only_banner, self.tag_overlay, self.progress_bar, self.tag_prompt):
                overlay.raise_()
            self.surface.when_ready(lambda clip=self.slideshow.current: self._play(clip))
        elif self.surface:
            self.surface.cancel_pending()
            self._hide_video()
