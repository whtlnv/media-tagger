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
    connection.close()


class Library:
    schema_version = 1  # the version this code writes; an opened library reports the version its tags.db records

    def __init__(self, drive_id, schema_version=schema_version):
        self.drive_id = drive_id
        self.schema_version = schema_version
        self._tags = {}

    @classmethod
    def create(cls, root):
        tags_db = _tags_db(root)
        tags_db.parent.mkdir()
        drive_id = str(uuid.uuid4())
        _write_meta(tags_db, drive_id=drive_id, schema_version=str(cls.schema_version))
        return cls(drive_id)

    @classmethod
    def open(cls, root):
        connection = sqlite3.connect(_tags_db(root))
        meta = dict(connection.execute("SELECT key, value FROM meta"))
        connection.close()
        return cls(meta["drive_id"], int(meta["schema_version"]))

    def enter(self, path, text):
        if text.startswith("-"):
            self._tags[path] = [tag for tag in self._tags[path] if tag != text[1:]]
            return
        self._tags[path] = sorted(set(text.split()))

    def tags(self, path):
        return self._tags.get(path, [])
