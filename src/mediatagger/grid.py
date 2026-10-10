from PySide6.QtCore import QStringListModel
from PySide6.QtWidgets import QListView

from mediatagger.folder import folder_entries


class Grid(QListView):
    def __init__(self, folder):
        super().__init__()
        self.setModel(QStringListModel([entry.name for entry in folder_entries(folder)], self))
