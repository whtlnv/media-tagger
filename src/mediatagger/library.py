class Library:
    drive_id = "drive"
    schema_version = 1

    @classmethod
    def create(cls, root):
        return cls()

    @classmethod
    def open(cls, root):
        return cls()

    def close(self):
        pass
