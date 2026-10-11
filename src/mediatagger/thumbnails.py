import subprocess

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QImageReader

from mediatagger.folder import is_video_name, subfolder_and_media_names

THUMBNAIL_SIZE = QSize(400, 400)  # the largest tile
TOOL_TIMEOUT_S = 15  # ffprobe/ffmpeg on a slow drive on a Pi; past this a hung tool leaves the tile's glyph


def image_thumbnail(path):
    """Decoded straight at thumbnail size: a 24-megapixel photo is never held whole in memory on a Pi."""
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and _larger_than_a_thumbnail(size):
        reader.setScaledSize(size.scaled(THUMBNAIL_SIZE, Qt.KeepAspectRatio))  # the stored size: rotation comes after
    image = reader.read()
    if image.isNull():
        return None
    return _shrunk_to_fit(image)


def _larger_than_a_thumbnail(size):
    return size.width() > THUMBNAIL_SIZE.width() or size.height() > THUMBNAIL_SIZE.height()


def _shrunk_to_fit(image):
    """Only ever smaller: a small picture keeps its own size, and the tile scales it when painting."""
    return image.scaled(THUMBNAIL_SIZE, Qt.KeepAspectRatio) if _larger_than_a_thumbnail(image.size()) else image


def _run_with_timeout(args, timeout, **kwargs):
    try:
        return subprocess.run(args, capture_output=True, timeout=timeout or TOOL_TIMEOUT_S, **kwargs)
    except (subprocess.TimeoutExpired, OSError):  # hung, or not installed
        return None


def video_duration(path, timeout=None):
    result = _run_with_timeout(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        timeout, text=True,
    )
    if result is None or result.returncode != 0:
        return None
    try:
        return float(result.stdout)
    except ValueError:  # "N/A": a stream or a file whose container records no duration
        return None


def video_thumbnail(path, timeout=None, duration=None):
    """A frame from about 10% in, past any fade-in or black first frame. The duration is probed unless given."""
    if duration is None:
        duration = video_duration(path, timeout=timeout)
    if duration is None:
        return None
    result = _run_with_timeout(
        ["ffmpeg", "-v", "error", "-ss", str(duration * 0.1), "-i", str(path),
         "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"],
        timeout,
    )
    frame = QImage.fromData(result.stdout) if result is not None else QImage()
    return None if frame.isNull() else _shrunk_to_fit(frame)


def folder_thumbnail(folder):
    """A folder shows its first image directly inside; with none there, it has no thumbnail."""
    first_image = next((name for name in subfolder_and_media_names(folder)[1] if not is_video_name(name)), None)
    return image_thumbnail(folder / first_image) if first_image else None


def thumbnail_and_duration(path):
    """What a grid tile shows for a file or folder; runs on a worker thread. Only a video has a duration."""
    if is_video_name(path.name):
        duration = video_duration(path)  # probed once: the frame is taken relative to it
        return (video_thumbnail(path, duration=duration) if duration is not None else None), duration
    if path.is_dir():
        return folder_thumbnail(path), None
    return image_thumbnail(path), None


def format_duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"
