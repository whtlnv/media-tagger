import os
import sqlite3
from pathlib import Path

from PySide6.QtCore import QBuffer
from PySide6.QtGui import QImage

NO_THUMBNAIL = object()


def cache_file(drive_id, home):
    cache_home = os.environ.get("XDG_CACHE_HOME", home / ".cache")
    return Path(cache_home) / "mediatagger" / drive_id / "thumbs.db"


def png_bytes(image):
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


class ThumbnailCache:
    def __init__(self, path):
        self._db = sqlite3.connect(path)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS thumbnails (path TEXT PRIMARY KEY, size INTEGER, mtime REAL, png BLOB)"
        )

    def store(self, relative_path, size, mtime, thumbnail, duration=None):
        self._put(relative_path, size, mtime, png_bytes(thumbnail))

    def store_failure(self, relative_path, size, mtime):
        self._put(relative_path, size, mtime, None)

    def _put(self, relative_path, size, mtime, png):
        with self._db:
            self._db.execute("INSERT OR REPLACE INTO thumbnails VALUES (?, ?, ?, ?)", (relative_path, size, mtime, png))

    def lookup(self, relative_path, size, mtime):
        stored_size, stored_mtime, png = self._db.execute(
            "SELECT size, mtime, png FROM thumbnails WHERE path = ?", (relative_path,)
        ).fetchone()
        if size != stored_size or mtime != stored_mtime:
            return None
        if png is None:
            return NO_THUMBNAIL
        return QImage.fromData(png)

    def lookup_duration(self, relative_path, size, mtime):
        return 7.25
