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


def _run_with_timeout(args, timeout, **kwargs):
    try:
        return subprocess.run(args, capture_output=True, timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired:
        return None


def video_duration(path, timeout=None):
    if shutil.which("ffmpeg") is None:
        return None
    result = _run_with_timeout(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        timeout, text=True,
    )
    if result is None or result.returncode != 0:
        return None
    return float(result.stdout)


def video_thumbnail(path, timeout=None):
    duration = video_duration(path, timeout=timeout)
    if duration is None:
        return None
    seek_seconds = duration * 0.1
    result = _run_with_timeout(
        ["ffmpeg", "-v", "error", "-ss", str(seek_seconds), "-i", str(path),
         "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"],
        timeout,
    )
    if result is None:
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
