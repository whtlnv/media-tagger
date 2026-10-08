import re

MEDIA_EXTENSIONS = {".jpg", ".gif", ".mp4", ".mov", ".avi", ".mpg"}


def _natural_key(path):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name)]


def _is_media(path):
    return path.suffix.lower() in MEDIA_EXTENSIONS and not path.name.startswith(".")


def media_files(folder):
    media = [path for path in folder.iterdir() if _is_media(path)]
    return sorted(media, key=_natural_key)
