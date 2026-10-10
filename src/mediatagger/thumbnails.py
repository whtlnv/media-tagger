from PySide6.QtCore import Qt
from PySide6.QtGui import QImage


def image_thumbnail(path):
    return QImage(str(path)).scaled(400, 400, Qt.KeepAspectRatio)
