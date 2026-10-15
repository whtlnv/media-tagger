import json

CONFIG_FILE = "mediatagger_config.json"
CONFIG_CANT_BE_READ_TEXT = f"{CONFIG_FILE} can't be read — no tiles marked"


def required_roots(drive):
    """The tag roots the drive's config says every file should have, and what is wrong with the config if anything.
    The config is only ever read, never written."""
    config = drive / CONFIG_FILE
    if not config.exists():
        return (), None
    try:
        settings = json.loads(config.read_text(encoding="utf-8"))
    except (OSError, ValueError):  # unreadable, not UTF-8 (UnicodeDecodeError) or not JSON (JSONDecodeError)
        return (), CONFIG_CANT_BE_READ_TEXT
    roots = settings.get("requiredRoots", []) if isinstance(settings, dict) else None
    if not isinstance(roots, list) or not all(isinstance(root, str) for root in roots):
        return (), CONFIG_CANT_BE_READ_TEXT
    return tuple(roots), None


def missing_roots(tags, roots):
    """How many of the roots none of the tags starts with."""
    return sum(not any(tag.startswith(root) for tag in tags) for root in roots)
