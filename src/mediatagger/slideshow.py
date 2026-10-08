from mediatagger.folder import media_files


class Slideshow:
    def __init__(self, current):
        self.current = current

    @classmethod
    def open(cls, folder):
        return cls(media_files(folder)[0])
