from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

# Explicit colours: the desktop theme's default text colour may be black, which vanishes on a black background.
LABEL_STYLE = "color: white; background-color: rgba(0, 0, 0, 160); padding: 8px 12px; border-radius: 6px; font-size: 18px;"
_DIMMED_LABEL_STYLE = LABEL_STYLE.replace("color: white", "color: grey")
CORNER_MARGIN = 16
NO_LIBRARY_TEXT = "No library open"
READ_ONLY_STATUS_TEXT = "Read-only — tags can't be saved"
TAGS_CANT_BE_SAVED_HERE_TEXT = "Tags can't be saved here"
RENAMED_TAG_TEXT = "✓ Renamed {} to {} on {:,} items"
_COULDNT_SAVE_TAGS_TEXT = "Couldn't save tags — is the drive still connected?"
_CANT_SAVE_MESSAGE_MS = 3000
_FINISHED_MESSAGE_MS = 3000


def overlay_label(text, parent):
    label = QLabel(text, parent)
    label.setStyleSheet(LABEL_STYLE)
    return label


def centre_in(label, bounds):
    """Size label to its text and centre it in bounds."""
    label.adjustSize()
    frame = label.geometry()
    frame.moveCenter(bounds.center())
    label.setGeometry(frame)


def pin_top_centre(label, bounds):
    """Centre label across the top of bounds, a corner margin down."""
    frame = label.geometry()
    frame.moveCenter(bounds.center())
    frame.moveTop(CORNER_MARGIN)
    label.setGeometry(frame)


class TagOverlay:
    """A file's own tags and, dimmed to their right, its inherited tags: two labels over the parent's top-right corner."""

    def __init__(self, parent):
        self.own = overlay_label("", parent)
        self.inherited = overlay_label("", parent)
        self.inherited.setStyleSheet(_DIMMED_LABEL_STYLE)
        self.hide()

    def show(self, tags):
        for label, shown in ((self.own, tags.own), (self.inherited, tags.inherited)):
            label.setText(" ".join(shown))
            label.adjustSize()
            label.setVisible(bool(shown))
            label.raise_()

    def hide(self):
        self.own.hide()
        self.inherited.hide()

    def raise_(self):
        self.own.raise_()
        self.inherited.raise_()

    def pin(self, pin_top_right):
        """Inherited tags sit in the top-right corner with the file's own tags just to their left."""
        pin_top_right(self.inherited)
        pin_top_right(self.own)
        if not self.inherited.isHidden():
            self.own.move(self.inherited.x() - self.own.width(), self.own.y())


class StatusBar(QWidget):
    """The always-visible strip along the bottom: the open library, the read-only notice, tagging messages, a problem
    with the drive's config and the one slot for background work."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.library_label = overlay_label(NO_LIBRARY_TEXT, self)
        self.read_only_status = overlay_label(READ_ONLY_STATUS_TEXT, self)
        self.read_only_status.hide()
        self.cant_save_status = overlay_label(TAGS_CANT_BE_SAVED_HERE_TEXT, self)
        self.cant_save_status.hide()
        self.couldnt_save_status = overlay_label(_COULDNT_SAVE_TAGS_TEXT, self)
        self.couldnt_save_status.hide()
        self.config_status = overlay_label("", self)
        self.config_status.hide()
        self.background_status = overlay_label("", self)
        self.background_status.hide()
        self.tags_status = overlay_label("", self)
        self.tags_status.hide()
        self.inherited_tags_status = overlay_label("", self)
        self.inherited_tags_status.setStyleSheet(_DIMMED_LABEL_STYLE)
        self.inherited_tags_status.hide()
        self._background_status_clearing = QTimer(self)
        self._background_status_clearing.setSingleShot(True)
        self._background_status_clearing.timeout.connect(self.background_status.hide)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(CORNER_MARGIN, 0, CORNER_MARGIN, CORNER_MARGIN)
        for label in (self.library_label, self.read_only_status, self.cant_save_status, self.couldnt_save_status, self.config_status, self.background_status, self.tags_status, self.inherited_tags_status):
            layout.addWidget(label)
        layout.addStretch()

    def place_along_the_bottom_of(self, rect):
        height = self.sizeHint().height()
        self.setGeometry(rect.left(), rect.bottom() + 1 - height, rect.width(), height)

    def show_library(self, text, read_only):
        """An open, writable library needs no mention: the label shows only what is wrong, or missing."""
        self.read_only_status.setVisible(read_only)
        self.library_label.setText(text)
        self.library_label.setVisible(bool(text))

    def show_config_problem(self, text):
        """What is wrong with the drive's config file, while that drive is open; nothing when it is fine or absent."""
        self.config_status.setText(text)
        self.config_status.setVisible(bool(text))

    def flash_cant_save(self):
        self.cant_save_status.show()
        QTimer.singleShot(_CANT_SAVE_MESSAGE_MS, self.cant_save_status.hide)

    def show_couldnt_save(self, shown):
        self.couldnt_save_status.setVisible(shown)

    def show_tags(self, text, inherited=""):
        self.tags_status.setText(text)
        self.tags_status.setVisible(bool(text))
        self.inherited_tags_status.setText(inherited)
        self.inherited_tags_status.setVisible(bool(inherited))

    def clear_background(self, starting_with):
        """Takes the background message off, if it is still one that starts so: a newer job's message stays."""
        if self.background_status.text().startswith(starting_with):
            self._background_status_clearing.stop()
            self.background_status.hide()

    def show_background(self, text, finished=False):
        """The one slot for background work. Work in progress and failures stay shown; a finished job's message clears
        after a few seconds, unless a newer message replaced it."""
        self._background_status_clearing.stop()
        self.background_status.setText(text)
        self.background_status.show()
        if finished:
            self._background_status_clearing.start(_FINISHED_MESSAGE_MS)
