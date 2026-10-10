import shutil
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QImageReader

from mediatagger.folder import media_files


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
    if result.returncode != 0:
        return None
    return float(result.stdout)


def video_thumbnail(path, timeout=None):
    duration = video_duration(path)
    if duration is None:
        return None
    seek_seconds = duration * 0.1
    try:
        result = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", str(seek_seconds), "-i", str(path),
             "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"],
            capture_output=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None
    return QImage.fromData(result.stdout).scaled(400, 400, Qt.KeepAspectRatio)


def folder_thumbnail(folder):
    return image_thumbnail(media_files(folder)[0])
