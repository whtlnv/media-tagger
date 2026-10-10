import os
import shutil
from pathlib import Path


def default_backup_root():
    return Path(os.environ["XDG_DATA_HOME"]) / "mediatagger" / "backups"


def back_up(library, backup_root=None, clock=None):
    if backup_root is None:
        backup_root = default_backup_root()
    backup_dir = backup_root / library.drive_id
    backup_dir.mkdir(parents=True)
    shutil.copy(library._tags_db, backup_dir / f"tags-{clock():%Y%m%dT%H%M%SZ}.db")
