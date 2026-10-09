import sqlite3
import uuid

LIBRARY_FOLDER = ".mediatagger"
CREATE_TAGS_TABLES = """
CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, rel_path TEXT UNIQUE, kind TEXT DEFAULT 'file');
CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS item_tags (item_id INTEGER, tag_id INTEGER);
"""


def tags_db_path(root):
    return root / LIBRARY_FOLDER / "tags.db"


def _init_tags_db(tags_db, **meta):
    connection = sqlite3.connect(tags_db)
    with connection:
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        connection.executemany(
            "INSERT INTO meta (key, value) VALUES (?, ?)", meta.items()
        )
        connection.executescript(CREATE_TAGS_TABLES)
    connection.close()


def _migrate_to_schema_version_2(connection):
    connection.executescript(CREATE_TAGS_TABLES)
    connection.execute("UPDATE meta SET value = '2' WHERE key = 'schema_version' AND value = '1'")


def _ensure_item_id(connection, rel_path):
    connection.execute("INSERT OR IGNORE INTO items (rel_path) VALUES (?)", (rel_path,))
    (item_id,) = connection.execute("SELECT id FROM items WHERE rel_path = ?", (rel_path,)).fetchone()
    return item_id


def _set_item_tags(connection, item_id, tags):
    connection.execute("DELETE FROM item_tags WHERE item_id = ?", (item_id,))
    connection.executemany("INSERT OR IGNORE INTO tags (name) VALUES (?)", [(tag,) for tag in tags])
    connection.executemany(
        "INSERT INTO item_tags (item_id, tag_id) SELECT ?, id FROM tags WHERE name = ?",
        [(item_id, tag) for tag in tags],
    )


def _parse_entry(text):
    words = text.lower().split()
    added = {word for word in words if not word.startswith("-")}
    removed = {word[1:] for word in words if word.startswith("-")}
    return added, removed


class Library:
    schema_version = 2  # the version this code writes; an opened library reports the version its tags.db records

    def __init__(self, tags_db, drive_id, schema_version=schema_version):
        self._tags_db = tags_db
        self.drive_id = drive_id
        self.schema_version = schema_version

    @classmethod
    def create(cls, root):
        tags_db = tags_db_path(root)
        tags_db.parent.mkdir(exist_ok=True)
        drive_id = str(uuid.uuid4())
        _init_tags_db(tags_db, drive_id=drive_id, schema_version=str(cls.schema_version))
        return cls(tags_db, drive_id)

    @classmethod
    def open(cls, root):
        tags_db = tags_db_path(root)
        connection = sqlite3.connect(tags_db)
        try:
            connection.execute("PRAGMA journal_mode = DELETE")
            with connection:
                _migrate_to_schema_version_2(connection)
        except sqlite3.OperationalError as error:
            if "locked" in str(error):
                raise
            # read-only drive: leave the library at its recorded schema version
        meta = dict(connection.execute("SELECT key, value FROM meta"))
        connection.close()
        return cls(tags_db, meta["drive_id"], int(meta["schema_version"]))

    def _key(self, path):
        return str(path.relative_to(self._tags_db.parent.parent))

    def enter(self, path, text):
        added, removed = _parse_entry(text)
        tags = (set(self.tags(path)) | added) - removed
        key = self._key(path)
        connection = sqlite3.connect(self._tags_db)
        with connection:
            _set_item_tags(connection, _ensure_item_id(connection, key), tags)
            if not tags:
                connection.execute("DELETE FROM items WHERE rel_path = ?", (key,))
        connection.close()

    def tags(self, path):
        if self.schema_version < 2:
            return []
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            "SELECT tags.name FROM item_tags"
            " JOIN items ON items.id = item_tags.item_id"
            " JOIN tags ON tags.id = item_tags.tag_id"
            " WHERE items.rel_path = ? ORDER BY tags.name",
            (self._key(path),),
        )
        tags = [tag for (tag,) in rows]
        connection.close()
        return tags
