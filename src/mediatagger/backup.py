import os
import sqlite3
from pathlib import Path


def default_backup_root():
    return Path(os.environ["XDG_DATA_HOME"]) / "mediatagger" / "backups"


def back_up(library, backup_root=None, clock=None):
    if backup_root is None:
        backup_root = default_backup_root()
    backup_dir = backup_root / library.drive_id
    backup_dir.mkdir(parents=True)
    _copy_database(library._tags_db, backup_dir / f"tags-{clock():%Y%m%dT%H%M%SZ}.db")


def _copy_database(source, destination):
    """SQLite's online backup API, not a file copy: the copy is consistent even while a connection has the source open."""
    reading = sqlite3.connect(source)
    writing = sqlite3.connect(destination)
    try:
        reading.backup(writing)
    finally:
        writing.close()
        reading.close()
