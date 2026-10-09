class Library:
    drive_id = "drive"

    @classmethod
    def create(cls, root):
        return cls()

    @classmethod
    def open(cls, root):
        return cls()

    def close(self):
        pass
