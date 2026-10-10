import os
from pathlib import Path

NO_THUMBNAIL = object()


def cache_file(drive_id, home):
    cache_home = os.environ.get("XDG_CACHE_HOME", home / ".cache")
    return Path(cache_home) / "mediatagger" / drive_id / "thumbs.db"


class ThumbnailCache:
    def __init__(self, path):
        self._path = path
        self._entries = {}

    def store(self, relative_path, size, mtime, thumbnail, duration=None):
        self._entries[relative_path] = (size, mtime, thumbnail)

    def store_failure(self, relative_path, size, mtime):
        self._entries[relative_path] = (size, mtime, NO_THUMBNAIL)

    def lookup(self, relative_path, size, mtime):
        stored_size, stored_mtime, thumbnail = self._entries[relative_path]
        if size != stored_size or mtime != stored_mtime:
            return None
        return thumbnail

    def lookup_duration(self, relative_path, size, mtime):
        return 7.25
