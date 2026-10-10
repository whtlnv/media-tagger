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
    """Copy the library's database into its drive's backup folder; any failure comes back as a BackupOutcome, never raised."""
    if backup_root is None:
        backup_root = default_backup_root()
    try:
        _back_up(library, backup_root / library.drive_id, clock)
    except (OSError, sqlite3.Error) as error:
        return BackupOutcome(failure=getattr(error, "strerror", None) or str(error))


def _back_up(library, backup_dir, clock):
    backup_dir.mkdir(parents=True, exist_ok=True)
    new_backup = backup_dir / f"{clock():{BACKUP_NAME_FORMAT}}.db"
    partial = new_backup.with_name(new_backup.name + ".partial")  # a half-written copy must never pass for a backup
    try:
        _copy_database(library._tags_db, partial)
    except (OSError, sqlite3.Error):
        partial.unlink(missing_ok=True)
        raise
    backups = sorted(backup_dir.glob(BACKUP_GLOB))
    if backups and backups[-1].read_bytes() == partial.read_bytes():
        partial.unlink()  # nothing changed since the latest backup
    else:
        partial.replace(new_backup)
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


def _copy_database(source, destination):
    """SQLite's online backup API, not a file copy: the copy is consistent even while a connection has the source open."""
    reading = sqlite3.connect(source)
    writing = sqlite3.connect(destination)
    try:
        reading.backup(writing)
    finally:
        writing.close()
        reading.close()
