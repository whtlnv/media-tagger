import os
from pathlib import Path

from PySide6.QtCore import QEventLoop, QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QImageIOHandler, QImageReader, QPainter
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QWidget

from mediatagger.folder import is_video
from mediatagger.library import LIBRARY_FOLDER, Library
from mediatagger.mpv_surface import MpvSurface
from mediatagger.slideshow import Slideshow
from mediatagger.video import VideoPlayer, new_engine

PLAYER_OPTIONS = {"vo": "libmpv"}
VIDEO_KEYS = {Qt.Key.Key_M: "m", Qt.Key.Key_P: "p", Qt.Key.Key_Up: "Up", Qt.Key.Key_Down: "Down", Qt.Key.Key_Return: "Enter"}
# Explicit colours: the desktop theme's default text colour may be black, which vanishes on a black background.
LABEL_STYLE = "color: white; background-color: rgba(0, 0, 0, 160); padding: 8px 12px; border-radius: 6px; font-size: 18px;"
CORNER_MARGIN = 16
TAG_PROMPT_WIDTH = 600
SLIDESHOW_KEYS = {Qt.Key.Key_Left: "Left", Qt.Key.Key_Right: "Right", Qt.Key.Key_Space: "Space"}
UNSUPPORTED_TEXT = "Unsupported"
APP_PACKAGE = Path(__file__).parent  # its drive is never written while the app runs
FULLSCREEN_SETTLE_MS = 1000
NO_LIBRARY_TEXT = "No library open"
LIBRARY_TEXT = "Library: {}"
NO_LIBRARY_VIEWING_ONLY_TEXT = "No library — viewing only"
DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT = "{} has no tag library — viewing only"
CREATE_LIBRARY_QUESTION = "Create a tag library on {}?"
READ_ONLY_BANNER_TEXT = "This drive is read-only — tags can't be saved"
READ_ONLY_STATUS_TEXT = "Read-only — tags can't be saved"


def overlay_label(text, parent):
    label = QLabel(text, parent)
    label.setStyleSheet(LABEL_STYLE)
    return label


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
    def __init__(self, path=None, player_options=None, folder_picker=None, is_mount_point=os.path.ismount, ask_to_create_library=None,
        app_location=APP_PACKAGE,
    ):
        super().__init__()
        self.is_mount_point = is_mount_point
        self.app_location = app_location
        self.ask_to_create_library = ask_to_create_library or self._ask_to_create_library
        self.declined_drives = set()
        self.library = None  # the open Library of the current drive, if it has one
        self.folder_picker = folder_picker or self._pick_folder
        self.slideshow = None
        self.video_player = VideoPlayer(new_engine(**{**PLAYER_OPTIONS, **(player_options or {})}))
        self.surface = None
        self._decoded_key = self._decoded = None
        self._tagging = None  # (library, path) of the item being tagged while the tag prompt is open
        self.tag_input = QLineEdit(self)
        self.tag_input.setStyleSheet(LABEL_STYLE)
        self.tag_input.returnPressed.connect(self._record_tags)
        self.tag_input.hide()
        self.prompt_tags = overlay_label("", self)
        self.prompt_tags.hide()
        self.tag_overlay = overlay_label("", self)
        self.tag_overlay.hide()
        self.info = overlay_label("", self)
        self.info.move(CORNER_MARGIN, CORNER_MARGIN)
        self.info.hide()
        self.placeholder = overlay_label(UNSUPPORTED_TEXT, self)
        self._build_status_bar()
        self.read_only_banner = overlay_label(READ_ONLY_BANNER_TEXT, self)
        self.read_only_banner.hide()
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setAcceptDrops(True)
        if path is None:
            self.placeholder.setText("Drop a folder or file here, or press o to open")
            return
        self._open(path)

    def _build_status_bar(self):
        self.status_bar = QWidget(self)
        self.library_label = overlay_label(NO_LIBRARY_TEXT, self.status_bar)
        self.read_only_status = overlay_label(READ_ONLY_STATUS_TEXT, self.status_bar)
        self.read_only_status.hide()
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(CORNER_MARGIN, 0, CORNER_MARGIN, CORNER_MARGIN)
        status_layout.addWidget(self.library_label)
        status_layout.addWidget(self.read_only_status)
        status_layout.addStretch()

    def closeEvent(self, event):
        if self.surface:
            self.surface.release()
        if self.video_player.engine.handle is not None:  # a second close must not call into a destroyed mpv handle
            self.video_player.engine.terminate()
        super().closeEvent(event)

    def resizeEvent(self, event):
        if self.surface:
            self.surface.setGeometry(self.rect())
        status_bar_height = self.status_bar.sizeHint().height()
        self.status_bar.setGeometry(0, self.height() - status_bar_height, self.width(), status_bar_height)
        self._centre(self.placeholder)
        self._pin_top_centre(self.read_only_banner)
        self._pin_top_right(self.tag_overlay)

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

    def _pin_above(self, label, widget):
        frame = label.geometry()
        frame.moveCenter(widget.geometry().center())
        frame.moveBottom(widget.geometry().top() - CORNER_MARGIN // 2)
        label.setGeometry(frame)

    def _pin_bottom_centre(self, widget):
        frame = widget.geometry()
        frame.moveCenter(self.rect().center())
        frame.moveBottom(self.status_bar.geometry().top() - 1)
        widget.setGeometry(frame)

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
        if event.key() == Qt.Key.Key_Escape and self._tag_prompt_has_focus():
            self._close_tag_prompt()
            return
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
        if event.key() == Qt.Key.Key_T:
            self._open_tag_prompt()
            return
        if self._tag_prompt_has_focus():
            return  # keys the open tag prompt ignores must not reach the slideshow or video
        if event.key() in VIDEO_KEYS:
            self.video_player.press(VIDEO_KEYS[event.key()])
            return
        if event.key() not in SLIDESHOW_KEYS:
            return
        key = SLIDESHOW_KEYS[event.key()]
        self.slideshow.press(key)
        self.video_player.press(key)
        self._refresh()
        self._show_current_tags()

    def _tag_prompt_has_focus(self):
        return self.focusWidget() is self.tag_input and self.tag_input.isVisible()

    def _open_tag_prompt(self):
        library = self.library
        path = self.slideshow.current
        self._tagging = (library, path)
        self.tag_overlay.hide()
        tags = " ".join(library.tags(path))
        self.prompt_tags.setText(tags)
        self.prompt_tags.adjustSize()
        self.tag_input.clear()
        self.tag_input.resize(min(TAG_PROMPT_WIDTH, self.width() - 2 * CORNER_MARGIN), self.tag_input.sizeHint().height())
        self._pin_bottom_centre(self.tag_input)
        self._pin_above(self.prompt_tags, self.tag_input)
        self.tag_input.show()
        self.tag_input.raise_()
        self.prompt_tags.setVisible(bool(tags))
        self.prompt_tags.raise_()
        self.tag_input.setFocus()

    def _record_tags(self):
        library, path = self._tagging
        library.enter(path, self.tag_input.text())
        self._close_tag_prompt()

    def _close_tag_prompt(self):
        self._show_tag_overlay(*self._tagging)
        self._tagging = None
        self.tag_input.hide()
        self.prompt_tags.hide()
        self.setFocus()  # keys go back to the viewer, not to the hidden input

    def _show_current_tags(self):
        if self.library:
            self._show_tag_overlay(self.library, self.slideshow.current)

    def _show_tag_overlay(self, library, path):
        tags = " ".join(library.tags(path))
        self.tag_overlay.setText(tags)
        self.tag_overlay.adjustSize()
        self._pin_top_right(self.tag_overlay)
        self.tag_overlay.setVisible(bool(tags))
        self.tag_overlay.raise_()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _ask_to_create_library(self, question):
        if not self.isVisible():
            self._show_and_settle()
        return QMessageBox(QMessageBox.Icon.Question, "", question, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self).exec() == QMessageBox.StandardButton.Yes

    def _show_and_settle(self):
        """macOS animates the switch to fullscreen; a modal opened mid-animation leaves the window at 100x30."""
        self.show()
        settling = QEventLoop()
        QTimer.singleShot(FULLSCREEN_SETTLE_MS, settling.quit)
        settling.exec()

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
        if showing_info:
            self.slideshow.press("i")
        self._refresh()
        self._open_library(path)  # after the first item is shown, so a question about the library is asked over it
        self._show_current_tags()

    def _open_library(self, path):
        self.library = None
        drive = next(folder for folder in (path, *path.parents) if self.is_mount_point(folder))
        if self._never_holds_a_library(drive):
            self.library_label.setText(NO_LIBRARY_VIEWING_ONLY_TEXT)
            return
        read_only = not os.access(drive, os.W_OK)
        if not (drive / LIBRARY_FOLDER / "tags.db").exists():
            if read_only:
                self._show_library_status(NO_LIBRARY_TEXT, read_only=True)
                return
            if not self._agrees_to_create_library(drive):
                self._show_library_status(DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT.format(drive.name), read_only=False)
                return
            self.library = Library.create(drive)
        else:
            self.library = Library.open(drive)
        self._show_library_status(LIBRARY_TEXT.format(drive.name), read_only)

    def _show_library_status(self, text, read_only):
        self.read_only_banner.setVisible(read_only)
        self.read_only_status.setVisible(read_only)
        self.library_label.setText(text)

    def _never_holds_a_library(self, drive):
        return drive == Path("/") or drive in self.app_location.parents

    def _agrees_to_create_library(self, drive):
        if drive in self.declined_drives:
            return False
        if not self.ask_to_create_library(CREATE_LIBRARY_QUESTION.format(drive.name)):
            self.declined_drives.add(drive)
            return False
        return True

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
            for overlay in (self.info, self.status_bar, self.read_only_banner, self.tag_overlay, self.prompt_tags, self.tag_input):
                overlay.raise_()
            self.surface.when_ready(lambda clip=self.slideshow.current: self._play(clip))
        elif self.surface:
            self.surface.cancel_pending()
            self.surface.hide()
