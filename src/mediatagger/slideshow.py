from mediatagger.folder import media_files


class Slideshow:
    def __init__(self, current):
        self.current = current
        self.overlay = None

    @classmethod
    def open(cls, path):
        if path.is_file():
            return cls(path)
        return cls(media_files(path)[0])

    def press(self, key):
        items = media_files(self.current.parent)
        index = items.index(self.current)
        if key == "i":
            self.overlay = _info(items, index)
            return
        step = -1 if key == "Left" else 1
        last = len(items) - 1
        index = max(0, min(index + step, last))
        self.current = items[index]
        if self.overlay:
            self.overlay = _info(items, index)


def _info(items, index):
    return f"{items[index].name} {index + 1} / {len(items)}"
