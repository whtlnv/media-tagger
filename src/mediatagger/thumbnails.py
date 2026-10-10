import shutil
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QImageReader

from mediatagger.folder import is_video, media_files


def image_thumbnail(path):
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    image = reader.read()
    if image.isNull():
        return None
    return image.scaled(400, 400, Qt.KeepAspectRatio)


def video_duration(path, timeout=None):
    if shutil.which("ffmpeg") is None:
        return None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    return float(result.stdout)


def video_thumbnail(path, timeout=None):
    duration = video_duration(path, timeout=timeout)
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
    images = [path for path in media_files(folder) if not is_video(path)]
    if not images:
        return None
    return image_thumbnail(images[0])


def format_duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"
