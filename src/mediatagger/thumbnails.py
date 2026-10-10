from PySide6.QtGui import QImage


def image_thumbnail(path):
    return QImage(str(path)).scaledToWidth(400)
