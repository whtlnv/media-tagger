import shutil
import sqlite3

from mediatagger.library import Library


def test_a_newly_created_library_reports_the_same_drive_id_after_it_is_closed_and_opened_again(tmp_path):
    created = Library.create(tmp_path)
    drive_id = created.drive_id

    reopened = Library.open(tmp_path)

    assert drive_id
    assert reopened.drive_id == drive_id


def test_a_newly_created_library_records_its_schema_version_alongside_its_drive_id(tmp_path):
    created = Library.create(tmp_path)
    schema_version = created.schema_version

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
    shutil.copytree(original_mount / ".mediatagger", new_mount / ".mediatagger")

    remounted = Library.open(new_mount)

    assert remounted.drive_id == drive_id


def test_tags_db_of_a_newly_created_library_is_an_sqlite_database_whose_meta_table_holds_the_drive_id_and_schema_version(tmp_path):
    created = Library.create(tmp_path)

    connection = sqlite3.connect(tmp_path / ".mediatagger" / "tags.db")
    try:
        meta = dict(connection.execute("SELECT key, value FROM meta"))
    finally:
        connection.close()

    assert meta["drive_id"] == created.drive_id
    assert int(meta["schema_version"]) == Library.schema_version


def test_a_library_created_removed_and_created_again_at_the_same_mount_point_reports_a_different_drive_id(tmp_path):
    first = Library.create(tmp_path)
    shutil.rmtree(tmp_path / ".mediatagger")

    second = Library.create(tmp_path)

    assert second.drive_id != first.drive_id


def test_an_opened_library_reports_the_schema_version_recorded_in_its_tags_db(tmp_path):
    Library.create(tmp_path)
    connection = sqlite3.connect(tmp_path / ".mediatagger" / "tags.db")
    with connection:
        connection.execute("UPDATE meta SET value = '0' WHERE key = 'schema_version'")
    connection.close()

    assert Library.open(tmp_path).schema_version == 0


def test_a_file_in_a_library_that_was_never_tagged_reports_no_tags(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    assert library.tags(photo) == []


def test_entering_beach_family_for_a_file_in_a_library_gives_that_file_the_tags_beach_and_family(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "beach family")

    assert sorted(library.tags(photo)) == ["beach", "family"]


def test_tags_entered_for_one_file_are_not_reported_for_another_file_in_the_same_library(tmp_path):
    library = Library.create(tmp_path)
    tagged = tmp_path / "beach.jpg"
    untagged = tmp_path / "office.jpg"
    tagged.touch()
    untagged.touch()

    library.enter(tagged, "beach family")

    assert library.tags(untagged) == []


def test_a_files_tags_are_reported_in_alphabetical_order_whatever_order_they_were_entered_in(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "family beach")

    assert library.tags(photo) == ["beach", "family"]


def test_entering_a_tag_a_file_already_has_does_not_report_it_twice(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "beach beach")

    assert library.tags(photo) == ["beach"]


def test_entering_minus_sunset_for_a_file_tagged_beach_and_sunset_leaves_it_tagged_only_beach(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()
    library.enter(photo, "beach sunset")

    library.enter(photo, "-sunset")

    assert library.tags(photo) == ["beach"]


def test_entering_minus_sunset_for_a_file_not_tagged_sunset_leaves_its_tags_unchanged(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()
    library.enter(photo, "beach family")

    library.enter(photo, "-sunset")

    assert library.tags(photo) == ["beach", "family"]


def test_one_entry_can_both_add_and_remove_tags(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()
    library.enter(photo, "sunset")

    library.enter(photo, "pool -sunset")

    assert library.tags(photo) == ["pool"]


def test_entered_tags_are_lowercased(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "Beach")

    assert library.tags(photo) == ["beach"]


def test_removing_is_case_insensitive(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()
    library.enter(photo, "beach sunset")

    library.enter(photo, "-Sunset")

    assert library.tags(photo) == ["beach"]


def test_extra_spaces_around_and_between_entered_tags_are_ignored(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "  beach   family ")

    assert library.tags(photo) == ["beach", "family"]


def test_an_entry_of_only_spaces_leaves_the_files_tags_unchanged(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()
    library.enter(photo, "beach family")

    library.enter(photo, "   ")

    assert library.tags(photo) == ["beach", "family"]


def test_a_lone_dash_in_an_entry_is_ignored(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "beach -")

    assert library.tags(photo) == ["beach"]


def test_hyphens_join_words_into_one_tag(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "day-at-beach")

    assert library.tags(photo) == ["day-at-beach"]


def test_a_colon_namespaced_tag_of_any_depth_is_kept_whole(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "place:mexico:cancun")

    assert library.tags(photo) == ["place:mexico:cancun"]


def test_a_files_tags_are_reported_again_after_its_library_is_closed_and_opened_again(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()
    library.enter(photo, "beach family")

    reopened = Library.open(tmp_path)

    assert reopened.tags(photo) == ["beach", "family"]


def test_a_files_tags_survive_the_drive_being_mounted_at_a_different_path(tmp_path):
    original_mount = tmp_path / "original"
    new_mount = tmp_path / "new"
    (original_mount / "trips").mkdir(parents=True)
    (new_mount / "trips").mkdir(parents=True)
    library = Library.create(original_mount)
    photo = original_mount / "trips" / "beach.jpg"
    photo.touch()
    library.enter(photo, "beach family")
    shutil.copytree(original_mount / ".mediatagger", new_mount / ".mediatagger")
    shutil.copy(photo, new_mount / "trips" / "beach.jpg")

    remounted = Library.open(new_mount)

    assert remounted.tags(new_mount / "trips" / "beach.jpg") == ["beach", "family"]


def test_a_library_whose_tags_db_holds_only_its_drive_id_and_schema_version_can_record_and_report_a_files_tags(tmp_path):
    (tmp_path / ".mediatagger").mkdir()
    connection = sqlite3.connect(tmp_path / ".mediatagger" / "tags.db")
    with connection:
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        connection.executemany(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            [("drive_id", "pre-tagging-drive"), ("schema_version", "1")],
        )
    connection.close()
    photo = tmp_path / "beach.jpg"
    photo.touch()
    library = Library.open(tmp_path)

    library.enter(photo, "beach family")

    assert library.tags(photo) == ["beach", "family"]


def test_tags_db_of_a_newly_created_library_records_each_file_and_tag_once_and_links_them_in_item_tags(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "beach family")

    connection = sqlite3.connect(tmp_path / ".mediatagger" / "tags.db")
    try:
        items = connection.execute("SELECT rel_path FROM items").fetchall()
        tags = connection.execute("SELECT name FROM tags ORDER BY name").fetchall()
        links = connection.execute(
            "SELECT items.rel_path, tags.name FROM item_tags"
            " JOIN items ON items.id = item_tags.item_id"
            " JOIN tags ON tags.id = item_tags.tag_id"
            " ORDER BY tags.name"
        ).fetchall()
    finally:
        connection.close()

    assert items == [("beach.jpg",)]
    assert tags == [("beach",), ("family",)]
    assert links == [("beach.jpg", "beach"), ("beach.jpg", "family")]
    assert library.tags(photo) == ["beach", "family"]


def test_opening_a_schema_version_1_library_upgrades_its_tags_db_in_place_to_schema_version_2(tmp_path):
    (tmp_path / ".mediatagger").mkdir()
    tags_db = tmp_path / ".mediatagger" / "tags.db"
    connection = sqlite3.connect(tags_db)
    with connection:
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        connection.executemany(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            [("drive_id", "phase-3-drive"), ("schema_version", "1")],
        )
    connection.close()

    Library.open(tmp_path)

    connection = sqlite3.connect(tags_db)
    try:
        meta = dict(connection.execute("SELECT key, value FROM meta"))
        tables = {name for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    finally:
        connection.close()

    assert meta["schema_version"] == "2"
    assert meta["drive_id"] == "phase-3-drive"
    assert {"items", "tags", "item_tags"} <= tables


def test_a_newly_created_library_records_schema_version_2_in_its_tags_db(tmp_path):
    Library.create(tmp_path)

    connection = sqlite3.connect(tmp_path / ".mediatagger" / "tags.db")
    try:
        meta = dict(connection.execute("SELECT key, value FROM meta"))
    finally:
        connection.close()

    assert meta["schema_version"] == "2"
