import os
from pathlib import Path


def test_every_test_runs_with_the_cache_home_pointing_at_a_throwaway_folder_outside_the_real_home():
    cache_home = Path(os.environ["XDG_CACHE_HOME"])

    assert (cache_home.is_dir(), cache_home.is_relative_to(Path.home())) == (True, False)


def test_with_the_cache_home_set_a_drives_cache_is_thumbs_db_under_mediatagger_and_the_drive_id(monkeypatch, tmp_path):
    from mediatagger.thumbnail_cache import cache_file

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))

    assert cache_file("drive-1234", home=tmp_path / "home") == tmp_path / "cache" / "mediatagger" / "drive-1234" / "thumbs.db"


def test_with_the_cache_home_unset_a_drives_cache_is_thumbs_db_under_the_homes_dot_cache(monkeypatch, tmp_path):
    from mediatagger.thumbnail_cache import cache_file

    monkeypatch.delenv("XDG_CACHE_HOME")

    assert cache_file("drive-1234", home=tmp_path / "home") == tmp_path / "home" / ".cache" / "mediatagger" / "drive-1234" / "thumbs.db"
