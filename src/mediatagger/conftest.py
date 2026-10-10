import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def backups_never_reach_the_real_home_folder(tmp_path_factory):
    """A viewer given no backup_root backs up under $XDG_DATA_HOME; point it at a throwaway folder for every test.
    Not via monkeypatch: requesting it here would set it up first and so tear it down last, after fixtures such as
    a test's mpv engine are gone, and undoing a setattr on a terminated engine raises."""
    previous = os.environ.get("XDG_DATA_HOME")
    os.environ["XDG_DATA_HOME"] = str(tmp_path_factory.mktemp("data-home"))
    yield
    if previous is None:
        os.environ.pop("XDG_DATA_HOME", None)
    else:
        os.environ["XDG_DATA_HOME"] = previous
