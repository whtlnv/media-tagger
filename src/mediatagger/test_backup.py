import json
import shutil
from datetime import datetime, timezone

from mediatagger.backup import back_up
from mediatagger.library import Library, tags_db_path


def _clock_at_october(day):
    return lambda: datetime(2026, 10, day, 15, 30, 0, tzinfo=timezone.utc)


def _library_with_photo(tmp_path):
    drive = tmp_path / "drive"
    drive.mkdir()
    photo = drive / "beach.jpg"
    photo.touch()
    return Library.create(drive), photo


def _backup_names(backup_root, library):
    return sorted(path.name for path in (backup_root / library.drive_id).glob("tags-*.db"))


def test_backing_up_a_library_writes_a_copy_of_its_tags_db_named_by_utc_time_under_the_drive_id_that_opens_with_its_tags(tmp_path):
    library, photo = _library_with_photo(tmp_path)
    library.enter(photo, "beach family")
    backup_root = tmp_path / "backups"

    back_up(library, backup_root=backup_root, clock=_clock_at_october(9))

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

    back_up(library, clock=_clock_at_october(9))

    assert (data_home / "mediatagger" / "backups" / library.drive_id / "tags-20261009T153000Z.db").is_file()


def test_backing_up_without_a_backup_root_writes_under_home_local_share_when_xdg_data_home_is_unset(tmp_path, monkeypatch):
    drive = tmp_path / "drive"
    drive.mkdir()
    library = Library.create(drive)
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)

    back_up(library, clock=_clock_at_october(9))

    assert (home / ".local" / "share" / "mediatagger" / "backups" / library.drive_id / "tags-20261009T153000Z.db").is_file()


def test_backing_up_writes_drive_json_next_to_the_drives_backups_recording_its_name_and_drive_id(tmp_path):
    drive = tmp_path / "PHOTOS"
    drive.mkdir()
    library = Library.create(drive)
    backup_root = tmp_path / "backups"

    back_up(library, backup_root=backup_root, clock=_clock_at_october(9))

    drive_json = json.loads((backup_root / library.drive_id / "drive.json").read_text())
    assert drive_json == {"name": "PHOTOS", "drive_id": library.drive_id}


def test_backing_up_a_drive_that_already_has_10_backups_leaves_only_the_10_newest_the_oldest_deleted(tmp_path):
    library, photo = _library_with_photo(tmp_path)
    backup_root = tmp_path / "backups"
    for day in range(1, 12):
        library.enter(photo, f"day{day}")
        back_up(library, backup_root=backup_root, clock=_clock_at_october(day))

    assert _backup_names(backup_root, library) == [f"tags-202610{day:02d}T153000Z.db" for day in range(2, 12)]


def test_backing_up_a_drive_that_has_fewer_than_10_backups_deletes_none_of_them(tmp_path):
    library, photo = _library_with_photo(tmp_path)
    backup_root = tmp_path / "backups"
    for day in range(1, 5):
        library.enter(photo, f"day{day}")
        back_up(library, backup_root=backup_root, clock=_clock_at_october(day))

    assert _backup_names(backup_root, library) == [f"tags-202610{day:02d}T153000Z.db" for day in range(1, 5)]


def test_backing_up_a_library_whose_database_has_not_changed_since_the_drives_last_backup_writes_no_new_backup(tmp_path):
    library, photo = _library_with_photo(tmp_path)
    library.enter(photo, "beach family")
    backup_root = tmp_path / "backups"
    back_up(library, backup_root=backup_root, clock=_clock_at_october(9))

    back_up(library, backup_root=backup_root, clock=_clock_at_october(10))

    assert _backup_names(backup_root, library) == ["tags-20261009T153000Z.db"]


def test_backing_up_a_library_whose_tags_changed_since_the_drives_last_backup_writes_a_new_backup(tmp_path):
    library, photo = _library_with_photo(tmp_path)
    library.enter(photo, "beach family")
    backup_root = tmp_path / "backups"
    back_up(library, backup_root=backup_root, clock=_clock_at_october(9))
    library.enter(photo, "beach sunset")

    back_up(library, backup_root=backup_root, clock=_clock_at_october(10))

    assert _backup_names(backup_root, library) == ["tags-20261009T153000Z.db", "tags-20261010T153000Z.db"]
