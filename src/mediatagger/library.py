import sqlite3
import uuid
from typing import NamedTuple

LIBRARY_FOLDER = ".mediatagger"
CREATE_TAGS_TABLES = """
CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, rel_path TEXT UNIQUE, kind TEXT DEFAULT 'file');
CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY, name TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS item_tags (item_id INTEGER, tag_id INTEGER);
"""
CREATE_MOMENTS_TABLE = (  # a chapter: a tag of a video at a moment, in whole tenths of a second
    "CREATE TABLE IF NOT EXISTS moments (item_id INTEGER, tag_id INTEGER, tenths INTEGER)"
)
_KEPT_MOMENTS = (  # moments of tags their item still has: a build from before chapters may have left others behind
    "moments JOIN items ON items.id = moments.item_id"
    " JOIN item_tags ON item_tags.item_id = moments.item_id AND item_tags.tag_id = moments.tag_id"
)
_SAME_MOMENT_WITHIN_TENTHS = 10  # two moments of a tag a second or less apart are one moment


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
        connection.execute(CREATE_MOMENTS_TABLE)
    connection.close()


_UPGRADES = {  # what brings a tags.db from the schema version before to the one named: only ever adding, never dropping
    2: [statement for statement in CREATE_TAGS_TABLES.split(";") if statement.strip()],
    3: [CREATE_MOMENTS_TABLE],
}


def _upgrade(connection, to_version):
    """Brings a tags.db of a known older schema version up to to_version in one transaction: all of it, or none of it.
    One of an unknown version is left as it is."""
    (recorded,) = connection.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    if recorded not in {str(version - 1) for version in _UPGRADES}:
        return
    connection.execute("BEGIN IMMEDIATE")  # DDL and executescript would otherwise run outside any transaction
    with connection:  # commits, or rolls everything back on any error
        for version in range(int(recorded) + 1, to_version + 1):
            for statement in _UPGRADES[version]:
                connection.execute(statement)
        connection.execute("UPDATE meta SET value = ? WHERE key = 'schema_version'", (str(to_version),))


def _tenths(seconds):
    return round(seconds * 10)


def _ensure_item_id(connection, rel_path, kind):
    connection.execute("INSERT OR IGNORE INTO items (rel_path, kind) VALUES (?, ?)", (rel_path, kind))
    (item_id,) = connection.execute("SELECT id FROM items WHERE rel_path = ?", (rel_path,)).fetchone()
    return item_id


def _drop_moments_of_tags_it_lacks(connection, item_id):
    connection.execute(
        "DELETE FROM moments WHERE item_id = ? AND tag_id NOT IN (SELECT tag_id FROM item_tags WHERE item_id = ?)", (item_id, item_id)
    )


def _set_item_tags(connection, item_id, tags):
    _drop_moments_of_tags_it_lacks(connection, item_id)  # any a build from before chapters left, so a tag added back can't revive them
    connection.execute("DELETE FROM item_tags WHERE item_id = ?", (item_id,))
    connection.executemany("INSERT OR IGNORE INTO tags (name) VALUES (?)", [(tag,) for tag in tags])
    connection.executemany(
        "INSERT INTO item_tags (item_id, tag_id) SELECT ?, id FROM tags WHERE name = ?",
        [(item_id, tag) for tag in tags],
    )
    _drop_moments_of_tags_it_lacks(connection, item_id)  # a tag the item no longer has takes its moments with it
    connection.execute("DELETE FROM tags WHERE id NOT IN (SELECT tag_id FROM item_tags)")


def _merge_tag(connection, old_id, new_id):
    """Every item tagged old_id is tagged new_id instead, its moments of old_id becoming moments of new_id."""
    connection.execute(  # a stale old moment would otherwise revive under the new tag
        "DELETE FROM moments WHERE tag_id = ? AND NOT EXISTS (SELECT 1 FROM item_tags"
        " WHERE item_id = moments.item_id AND tag_id = moments.tag_id)",
        (old_id,),
    )
    connection.execute(
        "DELETE FROM item_tags WHERE tag_id = ? AND item_id IN (SELECT item_id FROM item_tags WHERE tag_id = ?)",
        (old_id, new_id),
    )
    connection.execute("UPDATE item_tags SET tag_id = ? WHERE tag_id = ?", (new_id, old_id))
    connection.execute(  # an old moment within a second of a new one merges into it
        "DELETE FROM moments AS old WHERE tag_id = ? AND EXISTS (SELECT 1 FROM moments"
        f" WHERE item_id = old.item_id AND tag_id = ? AND abs(tenths - old.tenths) <= {_SAME_MOMENT_WITHIN_TENTHS})",
        (old_id, new_id),
    )
    connection.execute("UPDATE moments SET tag_id = ? WHERE tag_id = ?", (new_id, old_id))


def _parse_entry(text):
    words = text.lower().split()
    added = {word for word in words if not word.startswith("-")}
    removed = {word[1:] for word in words if word.startswith("-")}
    return added, removed


class EffectiveTags(NamedTuple):
    """An item's own tags, and the tags it inherits from its ancestor folders but doesn't have itself; each alphabetical."""

    own: list
    inherited: list


class Moment(NamedTuple):
    """A time in a video, in seconds to 0.1 s, and the tags marked there, alphabetical."""

    seconds: float
    tags: list


class Library:
    schema_version = 3  # the version this code writes; an opened library reports the version its tags.db records

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
            _upgrade(connection, cls.schema_version)
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

    @property
    def _has_tag_tables(self):
        return self.schema_version >= 2  # a read-only drive left at schema 1 has none

    @property
    def _has_moments_table(self):
        return self.schema_version >= 3  # a read-only drive left at an older schema has none

    def _key(self, path):
        return str(path.relative_to(self.root))

    def _direct_items_of(self, folder):
        """The prefix the folder's direct items' paths start with, and the condition and parameters matching their rows."""
        prefix = "" if folder == self.root else f"{self._key(folder)}/"
        condition = "substr(items.rel_path, 1, ?) = ? AND instr(substr(items.rel_path, ?), '/') = 0"
        return prefix, condition, (len(prefix), prefix, len(prefix) + 1)

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

    def add_chapter(self, video, text, seconds):
        """Every word of text becomes a tag of the video, marked at the moment seconds into it."""
        added, _removed = _parse_entry(text)
        tags = set(self.tags(video)) | added
        connection = sqlite3.connect(self._tags_db)
        with connection:
            item_id = _ensure_item_id(connection, self._key(video), "file")
            _set_item_tags(connection, item_id, tags)
            tenths = _tenths(seconds)
            connection.executemany(  # no second moment of a tag within a second of one it has
                "INSERT INTO moments (item_id, tag_id, tenths) SELECT ?, id, ? FROM tags WHERE name = ?"
                " AND NOT EXISTS (SELECT 1 FROM moments WHERE item_id = ? AND tag_id = tags.id"
                f" AND abs(tenths - ?) <= {_SAME_MOMENT_WITHIN_TENTHS})",
                [(item_id, tenths, tag, item_id, tenths) for tag in added],
            )
        connection.close()

    def delete_moment(self, video, seconds):
        """The video's moment at seconds goes; its tags stay on the video."""
        connection = sqlite3.connect(self._tags_db)
        with connection:
            connection.execute(
                "DELETE FROM moments WHERE tenths = ? AND item_id = (SELECT id FROM items WHERE rel_path = ?)",
                (_tenths(seconds), self._key(video)),
            )
        connection.close()

    def rename_tag(self, old, new):
        """Every item tagged old is tagged new instead."""
        connection = sqlite3.connect(self._tags_db)
        with connection:
            (changed,) = connection.execute(
                "SELECT COUNT(*) FROM item_tags JOIN tags ON tags.id = item_tags.tag_id WHERE tags.name = ?",
                (old,),
            ).fetchone()
            existing = connection.execute("SELECT id FROM tags WHERE name = ?", (new,)).fetchone()
            if existing is None:
                connection.execute("UPDATE tags SET name = ? WHERE name = ?", (new, old))
            else:
                (old_id,) = connection.execute("SELECT id FROM tags WHERE name = ?", (old,)).fetchone()
                _merge_tag(connection, old_id, existing[0])
        connection.close()
        return changed

    def moments(self, video):
        """The video's moments in time order."""
        if not self._has_moments_table:
            return []
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            f"SELECT moments.tenths, tags.name FROM {_KEPT_MOMENTS}"
            " JOIN tags ON tags.id = moments.tag_id"
            " WHERE items.rel_path = ? ORDER BY moments.tenths, tags.name",
            (self._key(video),),
        )
        moments = {}
        for tenths, tag in rows:
            moments.setdefault(tenths, []).append(tag)
        connection.close()
        return [Moment(tenths / 10, tags) for tenths, tags in moments.items()]

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
        _prefix, in_folder, parameters = self._direct_items_of(folder)
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            "SELECT items.rel_path, COUNT(*) FROM item_tags"
            " JOIN items ON items.id = item_tags.item_id"
            f" WHERE {in_folder}"
            " GROUP BY items.rel_path",
            parameters,
        )
        counts = {self.root / rel_path: count for rel_path, count in rows}
        connection.close()
        return counts

    def moment_counts(self, folder):
        """How many moments each of the folder's direct items has, for those with any, read in one query."""
        _prefix, in_folder, parameters = self._direct_items_of(folder)
        return {self.root / rel_path: count for rel_path, count in self._moment_counts(in_folder, parameters)}

    def all_moment_counts(self):
        """How many moments every item with any has, keyed by its full path as a string, read in one query."""
        root = f"{self.root}/"
        return {root + rel_path: count for rel_path, count in self._moment_counts("1", ())}

    def _moment_counts(self, condition, parameters):
        if not self._has_moments_table:
            return []
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            f"SELECT items.rel_path, COUNT(DISTINCT moments.tenths) FROM {_KEPT_MOMENTS}"
            f" WHERE {condition}"
            " GROUP BY items.rel_path",
            parameters,
        ).fetchall()
        connection.close()
        return rows

    def own_tags_in(self, folder):
        """The own tags of the folder's direct items, keyed by name, read in one query that looks only at that folder's rows."""
        if not self._has_tag_tables:
            return {}
        prefix, in_folder, parameters = self._direct_items_of(folder)
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            "SELECT items.rel_path, tags.name FROM item_tags"
            " JOIN items ON items.id = item_tags.item_id"
            " JOIN tags ON tags.id = item_tags.tag_id"
            f" WHERE {in_folder}",
            parameters,
        )
        tags = {}
        for rel_path, tag in rows:
            tags.setdefault(rel_path[len(prefix):], set()).add(tag)
        connection.close()
        return tags

    def tagged_items(self):
        """Every tagged item's kind and own tags, keyed by its path relative to the root, read in one query."""
        if not self._has_tag_tables:
            return {}
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            "SELECT items.rel_path, items.kind, tags.name FROM item_tags"
            " JOIN items ON items.id = item_tags.item_id"
            " JOIN tags ON tags.id = item_tags.tag_id"
        )
        items = {}
        for rel_path, kind, tag in rows:
            items.setdefault(rel_path, (kind, set()))[1].add(tag)
        connection.close()
        return items

    def own_tag_counts(self):
        """Every tagged item's own-tag count, keyed by its full path as a string, read in one query."""
        if not self._has_tag_tables:
            return {}
        root = f"{self.root}/"
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            "SELECT items.rel_path, COUNT(*) FROM item_tags JOIN items ON items.id = item_tags.item_id GROUP BY items.rel_path"
        )
        counts = {root + rel_path: count for rel_path, count in rows}
        connection.close()
        return counts

    def tags(self, path):
        key = self._key(path)
        return self._tags_by_key([key])[key]

    def effective_tags(self, path):
        ancestor_keys = [str(folder) for folder in path.relative_to(self.root).parents]
        key = self._key(path)
        tags_by_key = self._tags_by_key([key, *ancestor_keys])
        own = tags_by_key[key]
        inherited = sorted({tag for k in ancestor_keys for tag in tags_by_key[k]} - set(own))
        return EffectiveTags(own=own, inherited=inherited)

    def _tags_by_key(self, keys):
        if not self._has_tag_tables:
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
