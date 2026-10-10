import re

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic"}

VIDEO_EXTENSIONS = {".gif", ".mp4", ".mov", ".avi", ".mpg", ".mpeg", ".mkv", ".m4v", ".wmv", ".3gp"}

MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def _natural_key(path):
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", path.name)]


def _is_hidden(path):
    return path.name.startswith(".")


def _is_media(path):
    return path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS and not _is_hidden(path)


def _is_subfolder(path):
    return path.is_dir() and not _is_hidden(path)


def media_files(folder):
    media = [path for path in folder.iterdir() if _is_media(path)]
    return sorted(media, key=_natural_key)


def is_video(path):
    return path.suffix.lower() in VIDEO_EXTENSIONS


def folder_entries(folder):
    subfolders = [path for path in folder.iterdir() if _is_subfolder(path)]
    return sorted(subfolders, key=_natural_key) + media_files(folder)
