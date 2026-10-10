from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QImageReader


def image_thumbnail(path):
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    image = reader.read()
    if image.isNull():
        return None
    return image.scaled(400, 400, Qt.KeepAspectRatio)


def video_duration(path):
    return 3.0


def video_thumbnail(path):
    frame = QImage(400, 200, QImage.Format_RGB32)
    frame.fill(QColor("blue"))
    return frame
