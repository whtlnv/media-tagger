import shutil
import subprocess

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
    if shutil.which("ffmpeg") is None:
        return None
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    return float(result.stdout)


def video_thumbnail(path):
    if shutil.which("ffmpeg") is None:
        return None
    frame = QImage(400, 200, QImage.Format_RGB32)
    frame.fill(QColor("blue"))
    return frame
