import shutil
import sqlite3

from mediatagger.library import Library


def test_a_newly_created_library_reports_the_same_drive_id_after_it_is_closed_and_opened_again(tmp_path):
    created = Library.create(tmp_path)
    drive_id = created.drive_id
    created.close()

    reopened = Library.open(tmp_path)

    assert drive_id
    assert reopened.drive_id == drive_id


def test_a_newly_created_library_records_its_schema_version_alongside_its_drive_id(tmp_path):
    created = Library.create(tmp_path)
    schema_version = created.schema_version
    created.close()

    reopened = Library.open(tmp_path)

    assert schema_version
    assert reopened.schema_version == schema_version
    assert reopened.drive_id == created.drive_id


def test_two_libraries_created_on_different_drives_report_different_drive_ids(tmp_path):
    first_drive = tmp_path / "first"
    second_drive = tmp_path / "second"
    first_drive.mkdir()
    second_drive.mkdir()

    first = Library.create(first_drive)
    second = Library.create(second_drive)

    assert first.drive_id != second.drive_id


def test_a_library_reports_the_same_drive_id_when_its_drive_is_mounted_at_a_different_path(tmp_path):
    original_mount = tmp_path / "original"
    new_mount = tmp_path / "new"
    original_mount.mkdir()
    new_mount.mkdir()
    created = Library.create(original_mount)
    drive_id = created.drive_id
    created.close()
    shutil.copytree(original_mount / ".mediatagger", new_mount / ".mediatagger")

    remounted = Library.open(new_mount)

    assert remounted.drive_id == drive_id


def test_tags_db_of_a_newly_created_library_is_an_sqlite_database_whose_meta_table_holds_the_drive_id_and_schema_version(tmp_path):
    created = Library.create(tmp_path)
    created.close()

    connection = sqlite3.connect(tmp_path / ".mediatagger" / "tags.db")
    try:
        meta = dict(connection.execute("SELECT key, value FROM meta"))
    finally:
        connection.close()

    assert meta["drive_id"] == created.drive_id
    assert int(meta["schema_version"]) == Library.schema_version
