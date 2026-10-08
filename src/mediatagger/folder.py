import re


def _natural_key(path):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name)]


def media_files(folder):
    return sorted(folder.iterdir(), key=_natural_key)
