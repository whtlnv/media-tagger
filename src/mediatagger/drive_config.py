import json

CONFIG_FILE = "mediatagger_config.json"
CONFIG_CANT_BE_READ_TEXT = "mediatagger_config.json can't be read — no tiles marked"


def required_roots(drive):
    config = drive / CONFIG_FILE
    if not config.exists():
        return (), None
    try:
        json.loads(config.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return (), CONFIG_CANT_BE_READ_TEXT
    return ("type:", "size:"), None
