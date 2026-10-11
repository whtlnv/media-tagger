from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtWidgets import QCompleter, QLineEdit

_SUGGESTION_POPUP_STYLE = "QListView { color: white; background-color: rgb(64, 64, 64); border: 1px solid rgb(200, 200, 200); font-size: 18px; } QListView::item { padding: 4px 12px; }"
_TAG_INPUT_STYLE = "color: white; background-color: rgba(64, 64, 64, 220); border: 1px solid rgb(200, 200, 200); padding: 8px 12px; border-radius: 6px; font-size: 18px;"
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


class _TagInput(QLineEdit):
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Return:
            event.accept()  # QLineEdit passes Enter on to its parent, where it would pause the video
