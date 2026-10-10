import os
import re

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic"}

VIDEO_EXTENSIONS = {".gif", ".mp4", ".mov", ".avi", ".mpg", ".mpeg", ".mkv", ".m4v", ".wmv", ".3gp"}

MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def _natural_name_key(name):
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", name)]


def _natural_key(path):
    return _natural_name_key(path.name)


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


def is_video_name(name):
    return os.path.splitext(name)[1].lower() in VIDEO_EXTENSIONS


def subfolder_and_media_names(folder):
    """The names of a folder's subfolders and of its media, each in natural order, from one listing that stats no
    entry twice. Names, not Paths: parsing thousands of Path objects per open adds up on a Pi."""
    with os.scandir(folder) as scan:
        entries = [entry for entry in scan if not entry.name.startswith(".")]
    subfolders = [entry.name for entry in entries if entry.is_dir()]
    media = [entry.name for entry in entries if entry.is_file() and os.path.splitext(entry.name)[1].lower() in MEDIA_EXTENSIONS]
    return sorted(subfolders, key=_natural_name_key), sorted(media, key=_natural_name_key)


def folder_entries(folder):
    subfolders, media = subfolder_and_media_names(folder)
    return [folder / name for name in subfolders + media]
