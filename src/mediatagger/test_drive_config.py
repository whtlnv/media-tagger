import json

import pytest

from mediatagger.drive_config import CONFIG_CANT_BE_READ_TEXT, CONFIG_FILE, missing_roots, required_roots


def test_required_roots_of_a_drive_with_a_config_naming_two_roots_gives_them_and_no_problem(tmp_path):
    (tmp_path / CONFIG_FILE).write_text(json.dumps({"requiredRoots": ["type:", "size:"]}), encoding="utf-8")

    assert required_roots(tmp_path) == (("type:", "size:"), None)


def test_required_roots_of_a_drive_with_no_config_gives_no_roots_no_problem_and_writes_nothing(tmp_path):
    (tmp_path / "movie.mkv").write_bytes(b"")
    before = sorted(tmp_path.iterdir())

    assert required_roots(tmp_path) == ((), None)
    assert sorted(tmp_path.iterdir()) == before


@pytest.mark.parametrize("break_config", [
    pytest.param(lambda config: config.write_text("{not json", encoding="utf-8"), id="not valid JSON"),
    pytest.param(lambda config: config.write_text(json.dumps({"requiredRoots": "type:"}), encoding="utf-8"),
                 id="requiredRoots not a list of strings"),
    pytest.param(lambda config: config.mkdir(), id="cannot be read"),
])
def test_required_roots_of_a_drive_whose_config_is_broken_gives_no_roots_and_the_cant_be_read_problem(tmp_path, break_config):
    break_config(tmp_path / CONFIG_FILE)

    assert required_roots(tmp_path) == ((), CONFIG_CANT_BE_READ_TEXT)


def test_missing_roots_counts_the_roots_that_none_of_the_tags_starts_with():
    assert missing_roots(["type:photo", "beach"], ("type:", "size:")) == 1
