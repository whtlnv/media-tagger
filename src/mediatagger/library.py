class Library:
    schema_version = 1

    def __init__(self, root):
        self.drive_id = str(root)

    @classmethod
    def create(cls, root):
        return cls(root)

    @classmethod
    def open(cls, root):
        return cls(root)

    def close(self):
        pass
