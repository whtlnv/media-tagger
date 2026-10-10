import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

BACKUPS_KEPT_PER_DRIVE = 10


@dataclass
class BackupOutcome:
    failure: str


def default_backup_root():
    data_home = os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
    return Path(data_home) / "mediatagger" / "backups"


def back_up(library, backup_root=None, clock=None):
    if backup_root is None:
        backup_root = default_backup_root()
    backup_dir = backup_root / library.drive_id
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as error:
        return BackupOutcome(failure=error.strerror)
    new_backup = backup_dir / f"tags-{clock():%Y%m%dT%H%M%SZ}.db"
    previous_backups = sorted(backup for backup in backup_dir.glob("tags-*.db") if backup != new_backup)
    _copy_database(library._tags_db, new_backup)
    if _duplicates_latest(new_backup, previous_backups):
        new_backup.unlink()
    for old_backup in sorted(backup_dir.glob("tags-*.db"))[:-BACKUPS_KEPT_PER_DRIVE]:
        old_backup.unlink()
    drive_root = library._tags_db.parent.parent
    drive = {"name": drive_root.name, "drive_id": library.drive_id}
    (backup_dir / "drive.json").write_text(json.dumps(drive))


def _duplicates_latest(new_backup, previous_backups):
    return bool(previous_backups) and previous_backups[-1].read_bytes() == new_backup.read_bytes()


def _copy_database(source, destination):
    """SQLite's online backup API, not a file copy: the copy is consistent even while a connection has the source open."""
    reading = sqlite3.connect(source)
    writing = sqlite3.connect(destination)
    try:
        reading.backup(writing)
    finally:
        writing.close()
        reading.close()
