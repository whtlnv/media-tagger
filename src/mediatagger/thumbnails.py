from PySide6.QtCore import Qt
from PySide6.QtGui import QImageReader


def image_thumbnail(path):
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    return reader.read().scaled(400, 400, Qt.KeepAspectRatio)
