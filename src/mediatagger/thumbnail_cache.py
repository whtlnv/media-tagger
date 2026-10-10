import os
from pathlib import Path


def cache_file(drive_id, home):
    cache_home = os.environ.get("XDG_CACHE_HOME", home / ".cache")
    return Path(cache_home) / "mediatagger" / drive_id / "thumbs.db"


class ThumbnailCache:
    def __init__(self, path):
        self._path = path

    def store(self, relative_path, size, mtime, thumbnail):
        self._thumbnail = thumbnail

    def lookup(self, relative_path, size, mtime):
        return self._thumbnail
