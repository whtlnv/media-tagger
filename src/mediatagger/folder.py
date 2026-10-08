import re

MEDIA_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".gif",
    ".mp4", ".mov", ".avi", ".mpg", ".mpeg", ".mkv", ".m4v", ".wmv", ".3gp",
}


def _natural_key(path):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name)]


def _is_media(path):
    return path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS and not path.name.startswith(".")


def media_files(folder):
    media = [path for path in folder.iterdir() if _is_media(path)]
    return sorted(media, key=_natural_key)


def is_video(path):
    return path.suffix in {".gif", ".mp4", ".avi", ".mpg"}
