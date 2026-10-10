import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from mediatagger.library import tags_db_path

BACKUPS_KEPT_PER_DRIVE = 10
TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
BACKUP_NAME_FORMAT = f"tags-{TIMESTAMP_FORMAT}"
BACKUP_GLOB = "tags-*.db"


@dataclass
class BackupOutcome:
    failure: str


@dataclass
class FoundBackup:
    path: Path
    taken_at: datetime


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
    new_backup = backup_dir / f"{clock():{BACKUP_NAME_FORMAT}}.db"
    previous_backups = sorted(backup for backup in backup_dir.glob(BACKUP_GLOB) if backup != new_backup)
    try:
        _copy_database(library._tags_db, new_backup)
    except sqlite3.OperationalError as error:
        return BackupOutcome(failure=str(error))
    if _duplicates_latest(new_backup, previous_backups):
        new_backup.unlink()
    for old_backup in sorted(backup_dir.glob(BACKUP_GLOB))[:-BACKUPS_KEPT_PER_DRIVE]:
        old_backup.unlink()
    drive_root = library._tags_db.parent.parent
    drive = {"name": drive_root.name, "drive_id": library.drive_id}
    (backup_dir / "drive.json").write_text(json.dumps(drive))


def newest_backup(backup_root, drive_name):
    for drive_json in backup_root.glob("*/drive.json"):
        if json.loads(drive_json.read_text())["name"] != drive_name:
            continue
        backups = sorted(drive_json.parent.glob(BACKUP_GLOB))
        if not backups:
            continue
        path = backups[-1]
        taken_at = datetime.strptime(path.stem, BACKUP_NAME_FORMAT).replace(tzinfo=timezone.utc)
        return FoundBackup(path=path, taken_at=taken_at)


def restore(drive, backup, clock):
    tags_db = tags_db_path(drive)
    tags_db.rename(tags_db.parent / f"tags.db.damaged-{clock():{TIMESTAMP_FORMAT}}")
    _copy_database(backup, tags_db)


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
