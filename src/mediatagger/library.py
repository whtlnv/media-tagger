import sqlite3
import uuid
from typing import NamedTuple

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


def _ensure_item_id(connection, rel_path, kind):
    connection.execute("INSERT OR IGNORE INTO items (rel_path, kind) VALUES (?, ?)", (rel_path, kind))
    (item_id,) = connection.execute("SELECT id FROM items WHERE rel_path = ?", (rel_path,)).fetchone()
    return item_id


def _set_item_tags(connection, item_id, tags):
    connection.execute("DELETE FROM item_tags WHERE item_id = ?", (item_id,))
    connection.executemany("INSERT OR IGNORE INTO tags (name) VALUES (?)", [(tag,) for tag in tags])
    connection.executemany(
        "INSERT INTO item_tags (item_id, tag_id) SELECT ?, id FROM tags WHERE name = ?",
        [(item_id, tag) for tag in tags],
    )
    connection.execute("DELETE FROM tags WHERE id NOT IN (SELECT tag_id FROM item_tags)")


def _parse_entry(text):
    words = text.lower().split()
    added = {word for word in words if not word.startswith("-")}
    removed = {word[1:] for word in words if word.startswith("-")}
    return added, removed


class EffectiveTags(NamedTuple):
    """An item's own tags, and the tags it inherits from its ancestor folders but doesn't have itself; each alphabetical."""

    own: list
    inherited: list


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

    @property
    def root(self):
        return self._tags_db.parent.parent

    def _key(self, path):
        return str(path.relative_to(self.root))

    def enter(self, path, text):
        if path == self.root:
            return
        added, removed = _parse_entry(text)
        tags = (set(self.tags(path)) | added) - removed
        key = self._key(path)
        kind = "dir" if path.is_dir() else "file"
        connection = sqlite3.connect(self._tags_db)
        with connection:
            _set_item_tags(connection, _ensure_item_id(connection, key, kind), tags)
            if not tags:
                connection.execute("DELETE FROM items WHERE rel_path = ?", (key,))
        connection.close()

    def all_tags(self):
        connection = sqlite3.connect(self._tags_db)
        names = [
            name
            for (name,) in connection.execute(
                "SELECT tags.name FROM tags JOIN item_tags ON item_tags.tag_id = tags.id"
                " GROUP BY tags.id ORDER BY COUNT(*) DESC, tags.name"
            )
        ]
        connection.close()
        return names

    def tag_counts(self, folder):
        """The own-tag counts of the folder's direct items, read in one query that looks only at that folder's rows."""
        prefix = "" if folder == self.root else f"{self._key(folder)}/"
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            "SELECT items.rel_path, COUNT(*) FROM item_tags"
            " JOIN items ON items.id = item_tags.item_id"
            " WHERE substr(items.rel_path, 1, ?) = ? AND instr(substr(items.rel_path, ?), '/') = 0"
            " GROUP BY items.rel_path",
            (len(prefix), prefix, len(prefix) + 1),
        )
        counts = {self.root / rel_path: count for rel_path, count in rows}
        connection.close()
        return counts

    def items_tagged(self, tag):
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            "SELECT items.rel_path FROM item_tags"
            " JOIN items ON items.id = item_tags.item_id"
            " JOIN tags ON tags.id = item_tags.tag_id"
            " WHERE tags.name = ?",
            (tag,),
        )
        paths = [self.root / rel_path for (rel_path,) in rows]
        connection.close()
        return paths

    def tags(self, path):
        key = self._key(path)
        return self._tags_by_key([key])[key]

    def effective_tags(self, path):
        return self.effective_tags_of([path])[path]

    def effective_tags_of(self, paths):
        """Each path's effective tags, read in one query."""
        root = self.root
        relative = {path: path.relative_to(root) for path in paths}
        keys = {path: str(rel) for path, rel in relative.items()}
        ancestor_keys = {path: [str(folder) for folder in rel.parents] for path, rel in relative.items()}
        tags_by_key = self._tags_by_key(list({*keys.values(), *(k for ks in ancestor_keys.values() for k in ks)}))
        effective = {}
        for path in paths:
            own = tags_by_key[keys[path]]
            inherited = sorted({tag for k in ancestor_keys[path] for tag in tags_by_key[k]} - set(own))
            effective[path] = EffectiveTags(own=own, inherited=inherited)
        return effective

    def _tags_by_key(self, keys):
        if self.schema_version < 2:  # a read-only drive left at schema 1 has no tag tables
            return {k: [] for k in keys}
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            "SELECT items.rel_path, tags.name FROM item_tags"
            " JOIN items ON items.id = item_tags.item_id"
            " JOIN tags ON tags.id = item_tags.tag_id"
            f" WHERE items.rel_path IN ({', '.join('?' * len(keys))}) ORDER BY tags.name",
            keys,
        )
        tags_by_key = {k: [] for k in keys}
        for rel_path, tag in rows:
            tags_by_key[rel_path].append(tag)
        connection.close()
        return tags_by_key
