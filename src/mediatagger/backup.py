import shutil


def back_up(library, backup_root, clock):
    backup_dir = backup_root / library.drive_id
    backup_dir.mkdir(parents=True)
    shutil.copy(library._tags_db, backup_dir / f"tags-{clock():%Y%m%dT%H%M%SZ}.db")
