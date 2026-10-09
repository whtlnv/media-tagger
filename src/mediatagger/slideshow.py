from mediatagger.folder import media_files


class Slideshow:
    def __init__(self, current):
        self.current = current
        self.overlay = None

    @classmethod
    def open(cls, path):
        """The slideshow of a file's folder starting at it, or of a folder from its first item; None if it has none."""
        if path.is_file():
            return cls(path)
        items = media_files(path)
        return cls(items[0]) if items else None

    def press(self, key):
        items = media_files(self.current.parent)
        index = items.index(self.current)
        if key == "i":
            self.overlay = None if self.overlay else _info(items, index)
            return
        step = -1 if key == "Left" else 1
        last = len(items) - 1
        index = max(0, min(index + step, last))
        self.current = items[index]
        if self.overlay:
            self.overlay = _info(items, index)


def _info(items, index):
    return f"{items[index].name} {index + 1:,} / {len(items):,}"
