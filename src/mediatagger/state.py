import json
import os
from pathlib import Path

MOST_SEARCHES_REMEMBERED = 50


def state_file(home):
    """Where the last folder and the window geometry are remembered: under $XDG_CONFIG_HOME, else <home>/.config (the Pi's home, never a drive)."""
    config_home = os.environ.get("XDG_CONFIG_HOME", home / ".config")
    return Path(config_home) / "mediatagger" / "state.json"


def remembered_folder(state):
    folder = _remembered(state, "folder")
    return Path(folder) if folder is not None else None


def remember(state, folder, mount_point):
    remembering = _read(state)
    remembering["folder"] = str(folder)
    remembering["mount_point"] = str(mount_point)
    _write(state, remembering)


def remember_geometry(state, geometry):
    remembering = _read(state)
    remembering["geometry"] = geometry
    try:
        _write(state, remembering)
    except OSError:
        pass  # the window still closes; next time it opens centred


def remember_search(state, query):
    remembering = _read(state)
    earlier_searches = [search for search in remembered_searches(state) if search != query]
    remembering["searches"] = (earlier_searches + [query])[-MOST_SEARCHES_REMEMBERED:]
    try:
        _write(state, remembering)
    except OSError:
        pass  # the search still runs; it just isn't offered by ↑ next time


def remembered_searches(state):
    """The searches run before, oldest first; none if nothing is remembered."""
    return _remembered(state, "searches") or []


def remembered_geometry(state):
    return _remembered(state, "geometry")


def _remembered(state, key):
    return _read(state).get(key)


def _read(state):
    """What the state file remembers; nothing if it is missing, unreadable or not a JSON object."""
    try:
        remembering = json.loads(state.read_text())
    except (OSError, ValueError):
        return {}
    return remembering if isinstance(remembering, dict) else {}


def _write(state, remembering):
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(remembering))
