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
    schema_version = 1

    def __init__(self, drive_id):
        self.drive_id = drive_id

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
        (drive_id,) = connection.execute(
            "SELECT value FROM meta WHERE key = 'drive_id'"
        ).fetchone()
        connection.close()
        return cls(drive_id)
