import json
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


def test_backing_up_without_a_backup_root_writes_under_xdg_data_home_when_it_is_set(tmp_path, monkeypatch):
    drive = tmp_path / "drive"
    drive.mkdir()
    library = Library.create(drive)
    data_home = tmp_path / "data"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))

    back_up(library, clock=lambda: datetime(2026, 10, 9, 15, 30, 0, tzinfo=timezone.utc))

    assert (data_home / "mediatagger" / "backups" / library.drive_id / "tags-20261009T153000Z.db").is_file()


def test_backing_up_without_a_backup_root_writes_under_home_local_share_when_xdg_data_home_is_unset(tmp_path, monkeypatch):
    drive = tmp_path / "drive"
    drive.mkdir()
    library = Library.create(drive)
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)

    back_up(library, clock=lambda: datetime(2026, 10, 9, 15, 30, 0, tzinfo=timezone.utc))

    assert (home / ".local" / "share" / "mediatagger" / "backups" / library.drive_id / "tags-20261009T153000Z.db").is_file()


def test_backing_up_writes_drive_json_next_to_the_drives_backups_recording_its_name_and_drive_id(tmp_path):
    drive = tmp_path / "PHOTOS"
    drive.mkdir()
    library = Library.create(drive)
    backup_root = tmp_path / "backups"

    back_up(library, backup_root=backup_root, clock=lambda: datetime(2026, 10, 9, 15, 30, 0, tzinfo=timezone.utc))

    drive_json = json.loads((backup_root / library.drive_id / "drive.json").read_text())
    assert drive_json == {"name": "PHOTOS", "drive_id": library.drive_id}
