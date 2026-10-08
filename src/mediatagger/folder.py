import re

MEDIA_EXTENSIONS = {".jpg", ".gif", ".mp4", ".mov", ".avi", ".mpg"}


def _natural_key(path):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name)]


def media_files(folder):
    media = [
        path
        for path in folder.iterdir()
        if path.suffix.lower() in MEDIA_EXTENSIONS and not path.name.startswith(".")
    ]
    return sorted(media, key=_natural_key)
