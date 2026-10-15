import json

from mediatagger.drive_config import CONFIG_CANT_BE_READ_TEXT, CONFIG_FILE, missing_roots, required_roots


def test_required_roots_of_a_drive_with_a_config_naming_two_roots_gives_them_and_no_problem(tmp_path):
    (tmp_path / CONFIG_FILE).write_text(json.dumps({"requiredRoots": ["type:", "size:"]}), encoding="utf-8")

    assert required_roots(tmp_path) == (("type:", "size:"), None)


def test_required_roots_of_a_drive_with_no_config_gives_no_roots_no_problem_and_writes_nothing(tmp_path):
    (tmp_path / "movie.mkv").write_bytes(b"")
    before = sorted(tmp_path.iterdir())

    assert required_roots(tmp_path) == ((), None)
    assert sorted(tmp_path.iterdir()) == before


def test_required_roots_of_a_drive_whose_config_isnt_valid_json_gives_no_roots_and_the_cant_be_read_problem(tmp_path):
    (tmp_path / CONFIG_FILE).write_text("{not json", encoding="utf-8")

    assert required_roots(tmp_path) == ((), CONFIG_CANT_BE_READ_TEXT)


def test_required_roots_of_a_drive_whose_config_required_roots_isnt_a_list_of_strings_gives_no_roots_and_the_cant_be_read_problem(tmp_path):
    (tmp_path / CONFIG_FILE).write_text(json.dumps({"requiredRoots": "type:"}), encoding="utf-8")

    assert required_roots(tmp_path) == ((), CONFIG_CANT_BE_READ_TEXT)


def test_required_roots_of_a_drive_whose_config_cant_be_read_gives_no_roots_and_the_cant_be_read_problem(tmp_path):
    (tmp_path / CONFIG_FILE).mkdir()

    assert required_roots(tmp_path) == ((), CONFIG_CANT_BE_READ_TEXT)


def test_missing_roots_counts_the_roots_that_none_of_the_tags_starts_with():
    assert missing_roots(["type:photo", "beach"], ("type:", "size:")) == 1
