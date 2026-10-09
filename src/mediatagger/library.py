class Library:
    schema_version = 1

    def __init__(self, drive_id):
        self.drive_id = drive_id

    @classmethod
    def create(cls, root):
        library_dir = root / ".mediatagger"
        library_dir.mkdir()
        (library_dir / "tags.db").write_text(str(root))
        return cls(str(root))

    @classmethod
    def open(cls, root):
        return cls((root / ".mediatagger" / "tags.db").read_text())

    def close(self):
        pass
