import shutil
from datetime import datetime, timezone

from mediatagger.backup import back_up
from mediatagger.library import Library, tags_db_path


def test_backing_up_a_library_writes_a_copy_of_its_tags_db_named_by_utc_time_under_the_drive_id_that_opens_with_its_tags(tmp_path):
    drive = tmp_path / "drive"
    drive.mkdir()
    photo = drive / "beach.jpg"
    photo.touch()
    library = Library.create(drive)
    library.enter(photo, "beach family")
    backup_root = tmp_path / "backups"

    back_up(library, backup_root=backup_root, clock=lambda: datetime(2026, 10, 9, 15, 30, 0, tzinfo=timezone.utc))

    backup = backup_root / library.drive_id / "tags-20261009T153000Z.db"
    assert backup.is_file()
    restored_drive = tmp_path / "restored"
    tags_db_path(restored_drive).parent.mkdir(parents=True)
    shutil.copy(backup, tags_db_path(restored_drive))
    assert Library.open(restored_drive).tags(restored_drive / "beach.jpg") == ["beach", "family"]
