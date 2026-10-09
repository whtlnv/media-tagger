from mediatagger.folder import media_files


class Slideshow:
    """A folder's media in natural order, listed once when opened, with a position in it."""

    def __init__(self, items, index):
        self.items = items
        self.index = index
        self.overlay = None

    @property
    def current(self):
        return self.items[self.index]

    @classmethod
    def open(cls, path):
        """The slideshow of a file's folder starting at it, or of a folder from its first item; None if it has none."""
        folder = path.parent if path.is_file() else path
        items = media_files(folder)
        if not items:
            return None
        return cls(items, items.index(path) if path in items else 0)

    def press(self, key):
        if key == "i":
            self.overlay = None if self.overlay else self._info()
            return
        step = -1 if key == "Left" else 1
        self.index = max(0, min(self.index + step, len(self.items) - 1))
        if self.overlay:
            self.overlay = self._info()

    def _info(self):
        return f"{self.current.name} {self.index + 1:,} / {len(self.items):,}"
