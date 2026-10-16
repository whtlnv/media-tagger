import shutil
import sqlite3
from contextlib import contextmanager

import pytest

from mediatagger.library import Library


def _tags_db(root):
    return root / ".mediatagger" / "tags.db"


def _query(root, sql):
    connection = sqlite3.connect(_tags_db(root))
    try:
        return connection.execute(sql).fetchall()
    finally:
        connection.close()


def _read_meta(root):
    return dict(_query(root, "SELECT key, value FROM meta"))


@contextmanager
def _read_only_drive(root):
    tags_db = _tags_db(root)
    tags_db.chmod(0o444)
    tags_db.parent.chmod(0o555)
    root.chmod(0o555)
    try:
        yield
    finally:
        root.chmod(0o755)
        tags_db.parent.chmod(0o755)
        tags_db.chmod(0o644)


def _create_schema_version_1_library(root, drive_id):
    (root / ".mediatagger").mkdir()
    connection = sqlite3.connect(_tags_db(root))
    with connection:
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        connection.executemany(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            [("drive_id", drive_id), ("schema_version", "1")],
        )
    connection.close()


SCHEMA_VERSION_2_TABLES = """
CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, rel_path TEXT UNIQUE, kind TEXT DEFAULT 'file');
CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS item_tags (item_id INTEGER, tag_id INTEGER);
"""  # as the code of schema version 2 made them


def _create_schema_version_2_library(root, drive_id, tagged):
    """A tags.db as schema version 2 left it, its items tagged as given ({rel_path: (kind, [tags])})."""
    (root / ".mediatagger").mkdir()
    connection = sqlite3.connect(_tags_db(root))
    with connection:
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        connection.executemany("INSERT INTO meta (key, value) VALUES (?, ?)", [("drive_id", drive_id), ("schema_version", "2")])
        connection.executescript(SCHEMA_VERSION_2_TABLES)
    with connection:
        for rel_path, (kind, tags) in tagged.items():
            (item_id,) = connection.execute("INSERT INTO items (rel_path, kind) VALUES (?, ?) RETURNING id", (rel_path, kind)).fetchone()
            connection.executemany("INSERT OR IGNORE INTO tags (name) VALUES (?)", [(tag,) for tag in tags])
            connection.executemany(
                "INSERT INTO item_tags (item_id, tag_id) SELECT ?, id FROM tags WHERE name = ?", [(item_id, tag) for tag in tags]
            )
    connection.close()


TAGGED_ON_A_SCHEMA_VERSION_2_DRIVE = {
    "Trip": ("dir", ["place:mexico", "trip"]),
    "Trip/beach.jpg": ("file", ["beach", "family", "people:ana"]),
    "Trip/goal.mp4": ("file", ["goal", "sports"]),
    "notes.mov": ("file", ["family"]),
}


def _tag_rows(root):
    """Every row of the tag tables, as stored."""
    return [_query(root, f"SELECT * FROM {table} ORDER BY rowid") for table in ("items", "tags", "item_tags")]


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

    meta = _read_meta(tmp_path)

    assert meta["drive_id"] == created.drive_id
    assert int(meta["schema_version"]) == Library.schema_version


def test_a_library_created_removed_and_created_again_at_the_same_mount_point_reports_a_different_drive_id(tmp_path):
    first = Library.create(tmp_path)
    shutil.rmtree(tmp_path / ".mediatagger")

    second = Library.create(tmp_path)

    assert second.drive_id != first.drive_id


def test_an_opened_library_reports_the_schema_version_recorded_in_its_tags_db(tmp_path):
    Library.create(tmp_path)
    connection = sqlite3.connect(_tags_db(tmp_path))
    with connection:
        connection.execute("UPDATE meta SET value = '0' WHERE key = 'schema_version'")
    connection.close()

    assert Library.open(tmp_path).schema_version == 0


def test_a_file_in_a_library_that_was_never_tagged_reports_no_tags(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    assert library.tags(photo) == []


@pytest.mark.parametrize("entry, tags", [
    pytest.param("beach family", ["beach", "family"], id="beach family gives the tags beach and family"),
    pytest.param("family beach", ["beach", "family"], id="tags reported in alphabetical order whatever order entered"),
    pytest.param("beach beach", ["beach"], id="a tag entered twice is reported once"),
    pytest.param("Beach", ["beach"], id="entered tags are lowercased"),
    pytest.param("  beach   family ", ["beach", "family"], id="extra spaces around and between tags are ignored"),
    pytest.param("beach -", ["beach"], id="a lone dash is ignored"),
    pytest.param("day-at-beach", ["day-at-beach"], id="hyphens join words into one tag"),
    pytest.param("place:mexico:cancun", ["place:mexico:cancun"], id="a colon-namespaced tag of any depth is kept whole"),
])
def test_an_entry_for_an_untagged_file_in_a_library_gives_that_file_its_tags(tmp_path, entry, tags):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, entry)

    assert library.tags(photo) == tags


def test_tags_entered_for_one_file_are_not_reported_for_another_file_in_the_same_library(tmp_path):
    library = Library.create(tmp_path)
    tagged = tmp_path / "beach.jpg"
    untagged = tmp_path / "office.jpg"
    tagged.touch()
    untagged.touch()

    library.enter(tagged, "beach family")

    assert library.tags(untagged) == []


@pytest.mark.parametrize("tagged, entry, tags", [
    pytest.param("beach sunset", "-sunset", ["beach"], id="minus sunset on a file tagged beach and sunset leaves only beach"),
    pytest.param("beach family", "-sunset", ["beach", "family"], id="minus sunset on a file not tagged sunset leaves its tags unchanged"),
    pytest.param("sunset", "pool -sunset", ["pool"], id="one entry can both add and remove tags"),
    pytest.param("beach sunset", "-Sunset", ["beach"], id="removing is case-insensitive"),
    pytest.param("beach family", "   ", ["beach", "family"], id="an entry of only spaces leaves the tags unchanged"),
])
def test_an_entry_for_a_tagged_file_in_a_library_updates_its_tags(tmp_path, tagged, entry, tags):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()
    library.enter(photo, tagged)

    library.enter(photo, entry)

    assert library.tags(photo) == tags


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
    _create_schema_version_1_library(tmp_path, "pre-tagging-drive")
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

    items = _query(tmp_path, "SELECT rel_path FROM items")
    tags = _query(tmp_path, "SELECT name FROM tags ORDER BY name")
    links = _query(
        tmp_path,
        "SELECT items.rel_path, tags.name FROM item_tags"
        " JOIN items ON items.id = item_tags.item_id"
        " JOIN tags ON tags.id = item_tags.tag_id"
        " ORDER BY tags.name",
    )

    assert items == [("beach.jpg",)]
    assert tags == [("beach",), ("family",)]
    assert links == [("beach.jpg", "beach"), ("beach.jpg", "family")]
    assert library.tags(photo) == ["beach", "family"]


def test_opening_a_schema_version_1_library_upgrades_its_tags_db_in_place_to_schema_version_3_its_drive_id_unchanged(tmp_path):
    _create_schema_version_1_library(tmp_path, "phase-3-drive")

    Library.open(tmp_path)

    meta = _read_meta(tmp_path)
    tables = {name for (name,) in _query(tmp_path, "SELECT name FROM sqlite_master WHERE type = 'table'")}

    assert meta["schema_version"] == "3"
    assert meta["drive_id"] == "phase-3-drive"
    assert {"items", "tags", "item_tags"} <= tables


def test_opening_a_schema_version_2_library_upgrades_it_in_place_to_schema_version_3_its_drive_id_and_every_tag_unchanged(tmp_path):
    _create_schema_version_2_library(tmp_path, "phase-17-drive", TAGGED_ON_A_SCHEMA_VERSION_2_DRIVE)
    rows_before = _tag_rows(tmp_path)

    library = Library.open(tmp_path)

    assert _read_meta(tmp_path) == {"drive_id": "phase-17-drive", "schema_version": "3"}
    assert library.schema_version == 3
    assert _tag_rows(tmp_path) == rows_before
    for rel_path, (_kind, tags) in TAGGED_ON_A_SCHEMA_VERSION_2_DRIVE.items():
        assert library.tags(tmp_path / rel_path) == sorted(tags)


def test_a_newly_created_library_records_schema_version_3_in_its_tags_db(tmp_path):
    Library.create(tmp_path)

    meta = _read_meta(tmp_path)

    assert meta["schema_version"] == "3"


def test_a_schema_version_1_library_reports_schema_version_3_once_it_has_been_opened(tmp_path):
    _create_schema_version_1_library(tmp_path, "phase-3-drive")

    opened = Library.open(tmp_path)

    assert opened.schema_version == 3


def test_opening_a_schema_version_1_library_on_a_read_only_drive_writes_nothing_and_its_files_report_no_tags(tmp_path):
    _create_schema_version_1_library(tmp_path, "read-only-drive")
    photo = tmp_path / "beach.jpg"
    photo.touch()
    library_folder = tmp_path / ".mediatagger"
    tags_db = library_folder / "tags.db"
    before = tags_db.read_bytes()
    with _read_only_drive(tmp_path):
        library = Library.open(tmp_path)
        tags = library.tags(photo)

    assert tags == []
    assert tags_db.read_bytes() == before
    assert sorted(path.name for path in library_folder.iterdir()) == ["tags.db"]


def test_a_file_in_a_folder_of_a_schema_version_1_library_on_a_read_only_drive_has_no_own_and_no_inherited_effective_tags(tmp_path):
    _create_schema_version_1_library(tmp_path, "read-only-drive")
    (tmp_path / "Trip").mkdir()
    photo = tmp_path / "Trip" / "beach.jpg"
    photo.touch()
    with _read_only_drive(tmp_path):
        library = Library.open(tmp_path)
        tags = library.effective_tags(photo)

    assert (tags.own, tags.inherited) == ([], [])


def test_opening_a_schema_version_1_library_whose_upgrade_is_blocked_by_a_lock_on_tags_db_raises_the_error(tmp_path):
    _create_schema_version_1_library(tmp_path, "locked-drive")
    locker = sqlite3.connect(_tags_db(tmp_path))
    locker.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            Library.open(tmp_path)
    finally:
        locker.rollback()
        locker.close()


def test_a_tag_change_is_visible_to_a_separate_connection_to_tags_db_as_soon_as_it_is_entered(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()
    observer = sqlite3.connect(_tags_db(tmp_path))
    try:
        library.enter(photo, "beach family")

        tags = observer.execute("SELECT name FROM tags ORDER BY name").fetchall()
    finally:
        observer.close()

    assert tags == [("beach",), ("family",)]


def test_a_library_whose_tags_db_was_left_in_wal_mode_uses_the_rollback_journal_once_opened(tmp_path):
    Library.create(tmp_path)
    tags_db = _tags_db(tmp_path)
    connection = sqlite3.connect(tags_db)
    connection.execute("PRAGMA journal_mode = WAL")
    connection.close()

    Library.open(tmp_path)

    [(journal_mode,)] = _query(tmp_path, "PRAGMA journal_mode")

    assert journal_mode == "delete"


def test_removing_a_files_last_tag_removes_the_files_row_from_items(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()
    library.enter(photo, "beach")

    library.enter(photo, "-beach")

    items = _query(tmp_path, "SELECT rel_path FROM items")

    assert items == []


def test_a_tagged_files_row_in_items_records_its_kind_as_file(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "beach")

    items = _query(tmp_path, "SELECT rel_path, kind FROM items")

    assert items == [("beach.jpg", "file")]


def test_a_tagged_folders_row_in_items_records_its_kind_as_dir(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "trip"
    folder.mkdir()

    library.enter(folder, "beach")

    items = _query(tmp_path, "SELECT rel_path, kind FROM items")

    assert items == [("trip", "dir")]


def test_a_tagged_files_row_in_items_still_records_its_kind_as_file_next_to_a_tagged_folder(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "trip"
    folder.mkdir()
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(folder, "beach")
    library.enter(photo, "beach")

    items = _query(tmp_path, "SELECT rel_path, kind FROM items ORDER BY rel_path")

    assert items == [("beach.jpg", "file"), ("trip", "dir")]


def test_removing_a_tag_from_the_last_file_that_has_it_removes_the_tags_row_from_tags(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()
    other = tmp_path / "dunes.jpg"
    other.touch()
    library.enter(photo, "beach sunset")
    library.enter(other, "beach")

    library.enter(photo, "-sunset")

    tags = _query(tmp_path, "SELECT name FROM tags ORDER BY name")

    assert tags == [("beach",)]


def test_asking_the_library_for_a_folders_tag_counts_gives_an_item_with_two_own_tags_a_count_of_2(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "holiday"
    folder.mkdir()
    photo = folder / "beach.jpg"
    photo.touch()
    library.enter(photo, "beach family")

    counts = library.tag_counts(folder)

    assert counts[photo] == 2


def test_asking_the_library_for_a_folders_tag_counts_gives_an_untagged_item_no_count(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "holiday"
    folder.mkdir()
    photo = folder / "beach.jpg"
    photo.touch()

    counts = library.tag_counts(folder)

    assert photo not in counts


def test_a_folders_tag_counts_leave_out_tagged_items_that_live_in_other_folders_including_its_subfolders(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "holiday"
    subfolder = folder / "day1"
    subfolder.mkdir(parents=True)
    sibling = tmp_path / "holiday2"
    sibling.mkdir()
    nested_photo = subfolder / "beach.jpg"
    nested_photo.touch()
    sibling_photo = sibling / "dunes.jpg"
    sibling_photo.touch()
    library.enter(nested_photo, "beach")
    library.enter(sibling_photo, "dunes")

    counts = library.tag_counts(folder)

    assert counts == {}


def test_the_tag_counts_of_the_drives_top_folder_give_only_the_items_directly_in_it(tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "holiday").mkdir()
    for path in (tmp_path / "top.jpg", tmp_path / "holiday" / "beach.jpg"):
        path.touch()
        library.enter(path, "beach family")

    assert library.tag_counts(tmp_path) == {tmp_path / "top.jpg": 2}


def test_asking_the_library_for_the_tag_counts_of_a_folder_of_5000_items_runs_one_sql_query(tmp_path, monkeypatch):
    library = Library.create(tmp_path)
    folder = tmp_path / "holiday"
    folder.mkdir()
    for number in range(5000):
        (folder / f"photo{number:04}.jpg").touch()
    library.enter(folder / "photo0000.jpg", "beach")
    statements = []
    connect = sqlite3.connect

    def traced_connect(*args, **kwargs):
        connection = connect(*args, **kwargs)
        connection.set_trace_callback(statements.append)
        return connection

    monkeypatch.setattr(sqlite3, "connect", traced_connect)

    library.tag_counts(folder)

    assert len(statements) == 1


def test_entering_beach_for_a_folder_makes_beach_its_own_tag_also_after_the_library_is_reopened(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "trip"
    folder.mkdir()
    (folder / "beach.jpg").touch()

    library.enter(folder, "beach")

    assert library.tags(folder) == ["beach"]
    assert Library.open(tmp_path).tags(folder) == ["beach"]


def test_tagging_a_folder_leaves_every_file_inside_it_with_no_own_tags(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "trip"
    subfolder = folder / "day1"
    subfolder.mkdir(parents=True)
    photos = [folder / "beach.jpg", subfolder / "dunes.jpg"]
    for photo in photos:
        photo.touch()

    library.enter(folder, "beach")

    assert [library.tags(photo) for photo in photos] == [[], []]


def test_entering_tags_for_the_drives_mount_point_itself_stores_nothing_so_its_own_tags_read_back_empty(tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "beach.jpg").touch()

    library.enter(tmp_path, "beach")

    assert library.tags(tmp_path) == []
    assert Library.open(tmp_path).tags(tmp_path) == []


def test_entering_tags_for_a_folder_directly_under_the_drives_mount_point_stores_them_while_the_mount_point_stays_untagged(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "trip"
    folder.mkdir()

    library.enter(tmp_path, "sunset")
    library.enter(folder, "beach")

    assert library.tags(folder) == ["beach"]
    assert library.tags(tmp_path) == []
    assert _query(tmp_path, "SELECT rel_path, kind FROM items") == [("trip", "dir")]


def test_a_files_effective_tags_include_its_own_tags(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "beach.jpg"
    photo.touch()

    library.enter(photo, "beach family")

    assert library.effective_tags(photo).own == ["beach", "family"]


def test_a_files_effective_tags_include_the_own_tags_of_its_parent_folder_reported_as_inherited(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "trip"
    folder.mkdir()
    photo = folder / "dunes.jpg"
    photo.touch()

    library.enter(folder, "beach")

    assert library.effective_tags(photo).inherited == ["beach"]


def test_a_files_effective_tags_include_the_own_tags_of_every_ancestor_folder_up_to_the_drive_root_reported_as_inherited(tmp_path):
    library = Library.create(tmp_path)
    trip = tmp_path / "trip"
    day = trip / "day1"
    morning = day / "morning"
    morning.mkdir(parents=True)
    photo = morning / "dunes.jpg"
    photo.touch()

    library.enter(trip, "beach")
    library.enter(day, "sunset")

    assert sorted(library.effective_tags(photo).inherited) == ["beach", "sunset"]


def test_a_files_effective_tags_exclude_the_tags_of_a_sibling_folder_whose_name_is_a_prefix_of_its_parents(tmp_path):
    library = Library.create(tmp_path)
    trip = tmp_path / "trip"
    trip.mkdir()
    trip2 = tmp_path / "trip2"
    trip2.mkdir()
    photo = trip2 / "dunes.jpg"
    photo.touch()

    library.enter(trip, "beach")

    assert library.effective_tags(photo).inherited == []


def test_a_tag_a_file_has_both_as_its_own_and_from_an_ancestor_folder_appears_once_in_its_effective_tags_as_own(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "trip"
    folder.mkdir()
    photo = folder / "dunes.jpg"
    photo.touch()

    library.enter(folder, "beach")
    library.enter(photo, "beach")

    effective = library.effective_tags(photo)
    assert (effective.own, effective.inherited) == (["beach"], [])


def test_a_folders_effective_tags_include_the_own_tags_of_its_ancestor_folders_reported_as_inherited(tmp_path):
    library = Library.create(tmp_path)
    trip = tmp_path / "trip"
    day = trip / "day1"
    morning = day / "morning"
    morning.mkdir(parents=True)

    library.enter(trip, "beach")
    library.enter(day, "sunset")

    assert sorted(library.effective_tags(morning).inherited) == ["beach", "sunset"]


def test_reading_the_effective_tags_of_a_file_five_folders_deep_runs_one_sql_query(tmp_path, monkeypatch):
    library = Library.create(tmp_path)
    folder = tmp_path / "a" / "b" / "c" / "d" / "e"
    folder.mkdir(parents=True)
    photo = folder / "dunes.jpg"
    photo.touch()
    library.enter(tmp_path / "a", "beach")
    library.enter(photo, "sunset")
    statements = []
    connect = sqlite3.connect

    def traced_connect(*args, **kwargs):
        connection = connect(*args, **kwargs)
        connection.set_trace_callback(statements.append)
        return connection

    monkeypatch.setattr(sqlite3, "connect", traced_connect)

    library.effective_tags(photo)

    assert len(statements) == 1
