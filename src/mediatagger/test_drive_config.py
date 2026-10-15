import json

from mediatagger.drive_config import CONFIG_FILE, required_roots


def test_required_roots_of_a_drive_with_a_config_naming_two_roots_gives_them_and_no_problem(tmp_path):
    (tmp_path / CONFIG_FILE).write_text(json.dumps({"requiredRoots": ["type:", "size:"]}), encoding="utf-8")

    assert required_roots(tmp_path) == (("type:", "size:"), None)
