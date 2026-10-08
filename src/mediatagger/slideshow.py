from mediatagger.folder import media_files


class Slideshow:
    def __init__(self, current):
        self.current = current

    @classmethod
    def open(cls, path):
        if path.is_file():
            return cls(path)
        return cls(media_files(path)[0])

    def press(self, key):
        items = media_files(self.current.parent)
        step = -1 if key == "Left" else 1
        self.current = items[items.index(self.current) + step]
