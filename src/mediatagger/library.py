def _tags_db(root):
    return root / ".mediatagger" / "tags.db"


class Library:
    schema_version = 1

    def __init__(self, drive_id):
        self.drive_id = drive_id

    @classmethod
    def create(cls, root):
        tags_db = _tags_db(root)
        tags_db.parent.mkdir()
        tags_db.write_text(str(root))
        return cls(str(root))

    @classmethod
    def open(cls, root):
        return cls(_tags_db(root).read_text())

    def close(self):
        pass
