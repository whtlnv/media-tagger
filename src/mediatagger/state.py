import json
import os
from pathlib import Path


def state_file(home):
    """Where the last folder is remembered: under $XDG_CONFIG_HOME, else <home>/.config (the Pi's home, never a drive)."""
    config_home = os.environ.get("XDG_CONFIG_HOME", home / ".config")
    return Path(config_home) / "mediatagger" / "state.json"


def remembered_folder(state):
    if not state.exists():
        return None
    try:
        return Path(json.loads(state.read_text())["folder"])
    except (json.JSONDecodeError, KeyError):
        return None


def remember(state, folder, mount_point):
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"folder": str(folder), "mount_point": str(mount_point)}))
