from PySide6.QtCore import QStringListModel
from PySide6.QtWidgets import QListView

from mediatagger.folder import folder_entries


class Grid(QListView):
    def __init__(self, folder, at=None):
        super().__init__()
        names = [entry.name for entry in folder_entries(folder)]
        self.setModel(QStringListModel(names, self))
        if at is not None:
            self.setCurrentIndex(self.model().index(names.index(at.name), 0))
