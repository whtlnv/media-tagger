import json
import os
from pathlib import Path


def state_file(home):
    """Where the last folder is remembered: under $XDG_CONFIG_HOME, else <home>/.config (the Pi's home, never a drive)."""
    config_home = os.environ.get("XDG_CONFIG_HOME", home / ".config")
    return Path(config_home) / "mediatagger" / "state.json"


def remembered_folder(state):
    folder = _remembered(state, "folder")
    return Path(folder) if folder is not None else None


def remember(state, folder, mount_point):
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"folder": str(folder), "mount_point": str(mount_point)}))


def remembered_geometry(state):
    return _remembered(state, "geometry")


def _remembered(state, key):
    if not state.exists():
        return None
    try:
        return json.loads(state.read_text())[key]
    except (json.JSONDecodeError, KeyError, PermissionError):
        return None
