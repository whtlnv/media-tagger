import shutil
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QImageReader

from mediatagger.folder import is_video_name, subfolder_and_media_names


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
    """A folder shows its first image directly inside; with none there, it has no thumbnail."""
    first_image = next((name for name in subfolder_and_media_names(folder)[1] if not is_video_name(name)), None)
    return image_thumbnail(folder / first_image) if first_image else None


def thumbnail_and_duration(path):
    """What a grid tile shows for a file or folder; runs on a worker thread. Only a video has a duration."""
    if is_video_name(path.name):
        return video_thumbnail(path), video_duration(path)
    if path.is_dir():
        return folder_thumbnail(path), None
    return image_thumbnail(path), None


def format_duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"
