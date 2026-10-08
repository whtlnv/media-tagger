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
        step = -1 if key == "Left" else 1
        last = len(items) - 1
        self.current = items[max(0, min(items.index(self.current) + step, last))]
