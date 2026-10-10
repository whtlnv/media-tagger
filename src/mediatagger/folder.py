import os
import re
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic"}

VIDEO_EXTENSIONS = {".gif", ".mp4", ".mov", ".avi", ".mpg", ".mpeg", ".mkv", ".m4v", ".wmv", ".3gp"}

MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def _natural_key(path):
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", path.name)]


def _is_hidden(path):
    return path.name.startswith(".")


def _has_media_extension(path):
    return path.suffix.lower() in MEDIA_EXTENSIONS


def _is_media(path):
    return path.is_file() and _has_media_extension(path) and not _is_hidden(path)


def media_files(folder):
    media = [path for path in folder.iterdir() if _is_media(path)]
    return sorted(media, key=_natural_key)


def is_video(path):
    return path.suffix.lower() in VIDEO_EXTENSIONS


def folder_entries(folder):
    with os.scandir(folder) as scan:
        entries = [entry for entry in scan if not _is_hidden(entry)]
    subfolders = [Path(entry) for entry in entries if entry.is_dir()]
    media = [Path(entry) for entry in entries if entry.is_file() and _has_media_extension(Path(entry))]
    return sorted(subfolders, key=_natural_key) + sorted(media, key=_natural_key)
