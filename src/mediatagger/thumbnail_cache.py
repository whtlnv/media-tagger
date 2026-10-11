import os
import threading
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
    def __init__(self, path, root=None):
        self._root = root
        # Workers store what they generate while the GUI thread may look up: one connection, one at a time.
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS thumbnails (path TEXT PRIMARY KEY, size INTEGER, mtime REAL, png BLOB, duration REAL)"
        )

    def store(self, file_path, size, mtime, thumbnail, duration=None):
        self._put(file_path, size, mtime, png_bytes(thumbnail), duration)

    def store_failure(self, file_path, size, mtime):
        self._put(file_path, size, mtime, None)

    def _put(self, file_path, size, mtime, png, duration=None):
        with self._lock, self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO thumbnails VALUES (?, ?, ?, ?, ?)", (self._key(file_path), size, mtime, png, duration)
            )

    def _key(self, path):
        if self._root is None:
            return str(path)
        return str(path.relative_to(self._root))

    def lookup(self, file_path, size, mtime):
        with self._lock:
            row = self._db.execute(
                "SELECT size, mtime, png FROM thumbnails WHERE path = ?", (self._key(file_path),)
            ).fetchone()
        if row is None:
            return None
        stored_size, stored_mtime, png = row
        if size != stored_size or mtime != stored_mtime:
            return None
        if png is None:
            return NO_THUMBNAIL
        return QImage.fromData(png)

    def lookup_duration(self, file_path, size, mtime):
        with self._lock:
            (duration,) = self._db.execute("SELECT duration FROM thumbnails WHERE path = ?", (self._key(file_path),)).fetchone()
        return duration


def generate_through_cache(cache, generate, path):
    """Runs on a worker thread: a file's (thumbnail, duration, whether it had to be generated). A file whose size and
    mtime match what the cache holds is not generated again, nor is a stored failure retried until the file changes."""
    try:
        stat = path.stat()
    except OSError:  # gone since its folder was listed
        return None, None, False
    found = cache.lookup(path, stat.st_size, stat.st_mtime)
    if found is NO_THUMBNAIL:
        return None, None, False
    if found is not None:
        return found, cache.lookup_duration(path, stat.st_size, stat.st_mtime), False
    thumbnail, duration = generate(path)
    if thumbnail is None:
        cache.store_failure(path, stat.st_size, stat.st_mtime)
    else:
        cache.store(path, stat.st_size, stat.st_mtime, thumbnail, duration)
    return thumbnail, duration, True


def open_thumbnail_cache(drive_id, home, app_drive=None, viewed_drive=None):
    if drive_id is None:
        return ThumbnailCache(":memory:")
    path = cache_file(drive_id, home)
    if any(drive is not None and path.is_relative_to(drive) for drive in (app_drive, viewed_drive)):
        return ThumbnailCache(":memory:")
    path.parent.mkdir(parents=True, exist_ok=True)
    return ThumbnailCache(path, root=viewed_drive)  # keyed relative to the drive, wherever it is mounted
