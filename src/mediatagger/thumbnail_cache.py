import os
from pathlib import Path


def cache_file(drive_id, home):
    return Path(os.environ["XDG_CACHE_HOME"]) / "mediatagger" / drive_id / "thumbs.db"
