from PySide6.QtCore import QObject, Signal

WITH_TAGS = "With tags"

NO_TAGS = "No tags"

MISSING_TAGS = "Missing tags"


class GridFilter(QObject):
    """Which files the grids show: every one (no filter), or only those matching the one active filter. One per window,
    shared by every grid it opens, kept while the app runs."""

    changed = Signal()

    def __init__(self):
        super().__init__()
        self.active = None

    def choose(self, text):
        """Choosing the active filter again turns filtering off."""
        self.active = None if text == self.active else text
        self.changed.emit()

    def shows(self, tag_count, missing_roots):
        """Whether a file with this many own tags (what its tag badge counts) and missing roots is shown."""
        if self.active == WITH_TAGS:
            return tag_count > 0
        if self.active == NO_TAGS:
            return tag_count == 0
        if self.active == MISSING_TAGS:
            return missing_roots > 0
        return True
