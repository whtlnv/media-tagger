import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _pointed_at_a_throwaway_folder(variable, tmp_path_factory):
    """Not via monkeypatch: requesting it here would set it up first and so tear it down last, after fixtures such as
    a test's mpv engine are gone, and undoing a setattr on a terminated engine raises."""
    previous = os.environ.get(variable)
    os.environ[variable] = str(tmp_path_factory.mktemp(variable.lower()))
    yield
    if previous is None:
        os.environ.pop(variable, None)
    else:
        os.environ[variable] = previous


@pytest.fixture(autouse=True)
def backups_never_reach_the_real_home_folder(tmp_path_factory):
    """A viewer given no backup_root backs up under $XDG_DATA_HOME; point it at a throwaway folder for every test."""
    yield from _pointed_at_a_throwaway_folder("XDG_DATA_HOME", tmp_path_factory)


@pytest.fixture(autouse=True)
def state_never_reaches_the_real_home_folder(tmp_path_factory):
    """The window records the last folder under $XDG_CONFIG_HOME; point it at a throwaway folder for every test."""
    yield from _pointed_at_a_throwaway_folder("XDG_CONFIG_HOME", tmp_path_factory)


@pytest.fixture(autouse=True)
def thumbnails_never_reach_the_real_home_folder(tmp_path_factory):
    """Thumbnails are cached under $XDG_CACHE_HOME; point it at a throwaway folder for every test."""
    yield from _pointed_at_a_throwaway_folder("XDG_CACHE_HOME", tmp_path_factory)
