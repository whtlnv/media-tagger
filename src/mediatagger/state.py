import json
import os
from pathlib import Path

MOST_SEARCHES_REMEMBERED = 50


def state_file(home):
    """Where the last folder, the window geometry, the recent searches and the cheat sheet are remembered: under $XDG_CONFIG_HOME, else <home>/.config (the Pi's home, never a drive)."""
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
    _remember_if_writable(state, "geometry", geometry)  # unwritable, the window still closes; next time it opens centred


def remember_search(state, query):
    _remember_latest(state, "searches", query)  # unwritable, the search still runs; it just isn't offered by ↑ next time


def remember_cheat_sheet(state, shown):
    _remember_if_writable(state, "cheat_sheet", shown)  # unwritable, the sheet still toggles; next time it starts as it was before


def remembered_cheat_sheet(state):
    """Whether the key cheat sheet was showing; hidden if nothing is remembered."""
    return _remembered(state, "cheat_sheet") is True


def remembered_searches(state):
    """The searches run before, oldest first; none if nothing is remembered."""
    return _remembered(state, "searches") or []


def remember_rename(state, rename):
    _remember_latest(state, "renames", rename)  # unwritable, the rename still applies; it just isn't offered by ↑ next time


def remembered_renames(state):
    """The renames entered before, oldest first; none if nothing is remembered."""
    return _remembered(state, "renames") or []


def remembered_geometry(state):
    return _remembered(state, "geometry")


def _remember_latest(state, key, entry):
    """Adds entry as the newest of the list remembered under key, dropping an earlier copy and the oldest past the most kept."""
    earlier = [remembered for remembered in _remembered(state, key) or [] if remembered != entry]
    _remember_if_writable(state, key, (earlier + [entry])[-MOST_SEARCHES_REMEMBERED:])


def _remember_if_writable(state, key, value):
    remembering = _read(state)
    remembering[key] = value
    try:
        _write(state, remembering)
    except OSError:
        pass


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
