import sqlite3

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtWidgets import QCompleter, QLineEdit

from mediatagger.status_bar import CORNER_MARGIN, overlay_label

_SUGGESTION_POPUP_STYLE = "QListView { color: white; background-color: rgb(64, 64, 64); border: 1px solid rgb(200, 200, 200); font-size: 18px; } QListView::item { padding: 4px 12px; }"
TAG_INPUT_STYLE = "color: white; background-color: rgba(64, 64, 64, 220); border: 1px solid rgb(200, 200, 200); padding: 8px 12px; border-radius: 6px; font-size: 18px;"
_TAG_PROMPT_WIDTH = 600


def _last_word(text):
    return text.split(" ")[-1]


class _LastWordCompleter(QCompleter):
    def splitPath(self, path):
        return [_last_word(path).removeprefix("-")]

    def eventFilter(self, watched, event):
        if watched is self.popup() and event.type() == QEvent.Type.Move:
            self._open_above_the_prompt()
        if event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(watched, event)
        if event.key() == Qt.Key.Key_Tab and self.popup().currentIndex().isValid():
            self._accept_highlighted()
        if watched is self.popup() and event.key() == Qt.Key.Key_Return and self.popup().currentIndex().isValid():
            self._accept_highlighted()
            self.popup().hide()
            return True
        return super().eventFilter(watched, event)

    def _open_above_the_prompt(self):
        popup = self.popup()
        prompt_top = self.widget().mapToGlobal(QPoint(0, 0)).y()
        room_above = prompt_top - self.widget().window().mapToGlobal(QPoint(0, 0)).y()
        if popup.height() > room_above:
            popup.resize(popup.width(), room_above)  # the list scrolls rather than leaving the window
        popup.move(popup.x(), prompt_top - popup.height())

    def pathFromIndex(self, index):
        """What the prompt shows for a suggestion, on highlight or acceptance: its text with only the last word completed."""
        typed = self.widget().text()
        [word_being_completed] = self.splitPath(typed)
        return typed.removesuffix(word_being_completed) + index.data()

    def _accept_highlighted(self):
        self.widget().setText(self.pathFromIndex(self.popup().currentIndex()))


def give_tag_suggestions_to(input):
    """Suggestions completing the input's last word, whatever its case, in a popup styled like the prompts."""
    input.setCompleter(_LastWordCompleter([], input))
    input.completer().setCaseSensitivity(Qt.CaseInsensitive)
    input.completer().popup().setStyleSheet(_SUGGESTION_POPUP_STYLE)


def prompt_width(host):
    """A prompt's input width: fixed, but never wider than the host allows."""
    return min(_TAG_PROMPT_WIDTH, host.width() - 2 * CORNER_MARGIN)


def place_above_the_status_bar(host, status_bar, input, label):
    """The input at the bottom centre of the host, just above the status bar, with the label just above the input."""
    frame = input.geometry()
    frame.moveCenter(host.rect().center())
    frame.moveBottom(host.mapFromGlobal(status_bar.mapToGlobal(QPoint(0, 0))).y() - 1)
    input.setGeometry(frame)
    label_frame = label.geometry()
    label_frame.moveCenter(input.geometry().center())
    label_frame.moveBottom(input.geometry().top() - CORNER_MARGIN // 2)
    label.setGeometry(label_frame)


class TagInput(QLineEdit):
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Return:
            event.accept()  # QLineEdit passes Enter on to its parent, where it would pause the video


class TagPrompt:
    """The `t` prompt over a page: an input along the bottom centre, just above the status bar, with the item's own tags
    shown above it and suggestions completing the last word. Enter saves the entry into the library; a failure keeps the
    prompt open with its text and says so in the status bar."""

    def __init__(self, host, status_bar, on_close=lambda library, path: None):
        self._host = host
        self._status_bar = status_bar
        self._on_close = on_close
        self._tagging = None  # (library, path) of the item being tagged while the prompt is open
        self._enter = None  # what saves the entry, if not the library's own tag entry
        self._suggestions = ([], [])
        self.input = TagInput(host)
        self.input.setStyleSheet(TAG_INPUT_STYLE)
        self.input.returnPressed.connect(self._record_tags)
        self.input.textEdited.connect(self._offer_suggestions)
        give_tag_suggestions_to(self.input)
        self.input.hide()
        self.shown_tags = overlay_label("", host)
        self.shown_tags.hide()

    def is_open(self):
        return self._tagging is not None

    def has_focus(self):
        return self._host.focusWidget() is self.input and self.input.isVisible()

    def open(self, library, path, enter=None):
        """Enter saves the entry with enter(path, text), by default the library's own tag entry."""
        self._tagging = (library, path)
        self._enter = enter
        item_tags = library.tags(path)
        tags = " ".join(item_tags)
        self.shown_tags.setText(tags)
        self.shown_tags.adjustSize()
        self.input.clear()
        self._suggestions = ([tag for tag in library.all_tags() if tag not in item_tags], item_tags)
        self._offer_suggestions("")
        self.input.resize(prompt_width(self._host), self.input.sizeHint().height())
        self.place()
        self.input.show()
        self.shown_tags.setVisible(bool(tags))
        self.raise_()
        self.input.setFocus()

    def place(self):
        """At the bottom centre of the host, just above the status bar, with the shown tags just above the input."""
        place_above_the_status_bar(self._host, self._status_bar, self.input, self.shown_tags)

    def raise_(self):
        self.input.raise_()
        self.shown_tags.raise_()

    def close(self):
        library, path = self._tagging
        self._tagging = None
        self.input.hide()
        self.shown_tags.hide()
        self._status_bar.show_couldnt_save(False)  # it was about this prompt's entry
        self._host.setFocus()  # keys go back to the host, not to the hidden input
        self._on_close(library, path)

    def _offer_suggestions(self, text):
        to_add, to_remove = self._suggestions
        removing = _last_word(text).startswith("-")
        candidates = to_remove if removing else to_add
        entered = [word.removeprefix("-") for word in text.lower().split(" ")[:-1]]
        self.input.completer().model().setStringList([tag for tag in candidates if tag not in entered])

    def _record_tags(self):
        library, path = self._tagging
        try:
            (self._enter or library.enter)(path, self.input.text())
        except (sqlite3.Error, OSError):
            self._status_bar.show_couldnt_save(True)
            return
        self.close()
