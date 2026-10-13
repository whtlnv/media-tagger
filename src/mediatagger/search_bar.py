from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit

from mediatagger.state import remembered_searches


class SearchBar(QLineEdit):
    """The one-line search box above the grid. Enter submits its query and Esc a blank one, closing it either way;
    ↑ and ↓ step through the searches remembered in the state file."""

    submitted = Signal(str)

    def __init__(self, state_file, parent=None):
        super().__init__(parent)
        self._state_file = state_file
        self._recalled = 0
        self.hide()

    def open(self):
        self._recalled = 0
        self.clear()
        self.show()
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            self.submitted.emit(self.text())
            return
        if event.key() == Qt.Key.Key_Escape:
            self.submitted.emit("")
            return
        if event.key() == Qt.Key.Key_Up:
            self.recall_older_search()
            return
        if event.key() == Qt.Key.Key_Down:
            self.recall_newer_search()
            return
        super().keyPressEvent(event)

    def recall_newer_search(self):
        """Each call puts the next newer remembered search in the search bar, emptying it past the newest."""
        if not self._recalled:
            return  # nothing recalled yet: what was typed stays
        self._recalled -= 1
        self.setText(remembered_searches(self._state_file)[-self._recalled] if self._recalled else "")

    def recall_older_search(self):
        """Each call puts the next older remembered search in the search bar, stopping at the oldest."""
        searches = remembered_searches(self._state_file)
        if not searches:
            return
        self._recalled = min(self._recalled + 1, len(searches))
        self.setText(searches[-self._recalled])
