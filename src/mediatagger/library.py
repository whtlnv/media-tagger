import sqlite3
import uuid

LIBRARY_FOLDER = ".mediatagger"


def _tags_db(root):
    return root / LIBRARY_FOLDER / "tags.db"


def _write_meta(tags_db, **meta):
    connection = sqlite3.connect(tags_db)
    with connection:
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        connection.executemany(
            "INSERT INTO meta (key, value) VALUES (?, ?)", meta.items()
        )
        connection.execute("CREATE TABLE tags (path TEXT, tag TEXT)")
    connection.close()


class Library:
    schema_version = 1  # the version this code writes; an opened library reports the version its tags.db records

    def __init__(self, tags_db, drive_id, schema_version=schema_version):
        self._tags_db = tags_db
        self.drive_id = drive_id
        self.schema_version = schema_version

    @classmethod
    def create(cls, root):
        tags_db = _tags_db(root)
        tags_db.parent.mkdir()
        drive_id = str(uuid.uuid4())
        _write_meta(tags_db, drive_id=drive_id, schema_version=str(cls.schema_version))
        return cls(tags_db, drive_id)

    @classmethod
    def open(cls, root):
        tags_db = _tags_db(root)
        connection = sqlite3.connect(tags_db)
        meta = dict(connection.execute("SELECT key, value FROM meta"))
        connection.close()
        return cls(tags_db, meta["drive_id"], int(meta["schema_version"]))

    def enter(self, path, text):
        words = text.lower().split()
        removed = {word[1:] for word in words if word.startswith("-")}
        added = {word for word in words if not word.startswith("-")}
        tags = (set(self.tags(path)) | added) - removed
        connection = sqlite3.connect(self._tags_db)
        with connection:
            connection.execute("DELETE FROM tags WHERE path = ?", (str(path),))
            connection.executemany(
                "INSERT INTO tags (path, tag) VALUES (?, ?)",
                [(str(path), tag) for tag in tags],
            )
        connection.close()

    def tags(self, path):
        connection = sqlite3.connect(self._tags_db)
        rows = connection.execute(
            "SELECT tag FROM tags WHERE path = ? ORDER BY tag", (str(path),)
        )
        tags = [tag for (tag,) in rows]
        connection.close()
        return tags
