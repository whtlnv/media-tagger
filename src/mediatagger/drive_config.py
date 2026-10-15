CONFIG_FILE = "mediatagger_config.json"


def required_roots(drive):
    if not (drive / CONFIG_FILE).exists():
        return (), None
    return ("type:", "size:"), None
