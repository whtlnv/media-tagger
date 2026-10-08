from mediatagger.folder import media_files


class Slideshow:
    def __init__(self, current):
        self.current = current

    @classmethod
    def open(cls, path):
        if path.is_file():
            return cls(path)
        return cls(media_files(path)[0])
