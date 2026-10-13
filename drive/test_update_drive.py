import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UPDATE_DRIVE = REPO / "drive" / "update-drive.sh"
PACKAGE = REPO / "src" / "mediatagger"


def update_drive(drive, env=None):
    subprocess.run(["sh", str(UPDATE_DRIVE), str(drive)], check=True, env=env)


def empty_drive(tmp_path):
    drive = tmp_path / "drive"
    drive.mkdir()
    return drive


def app_on(drive):
    return drive / "mediatagger" / "app" / "mediatagger"


def version_on(drive):
    return drive / "mediatagger" / "app" / "VERSION"


def modules_on_drive_after_update(tmp_path):
    drive = empty_drive(tmp_path)

    update_drive(drive)

    return {p.name for p in app_on(drive).glob("*.py")}


def test_update_drive_puts_every_non_test_module_into_the_drive_app(tmp_path):
    on_drive = modules_on_drive_after_update(tmp_path)

    modules = {
        p.name
        for p in PACKAGE.glob("*.py")
        if not p.name.startswith("test_") and p.name != "conftest.py"
    }
    assert modules <= on_drive
    assert "__init__.py" in on_drive


def test_update_drive_leaves_test_modules_and_conftest_out_of_the_drive_app(tmp_path):
    on_drive = modules_on_drive_after_update(tmp_path)

    leaked = {name for name in on_drive if name.startswith("test_") or name == "conftest.py"}
    assert leaked == set()


def env_with_python313_on_path(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3.13").write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    (bin_dir / "python3.13").chmod(0o755)
    return {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}


def test_update_drive_leaves_unchecked_hash_bytecode_next_to_every_module_in_the_drive_app(tmp_path):
    env = env_with_python313_on_path(tmp_path)
    drive = empty_drive(tmp_path)

    update_drive(drive, env=env)

    app = app_on(drive)
    unchecked_hash = 0b01
    flags = {
        module.name: int.from_bytes(pyc.read_bytes()[4:8], "little") if pyc.exists() else None
        for module in app.glob("*.py")
        for pyc in [Path(importlib.util.cache_from_source(str(module)))]
    }
    assert flags and flags == {name: unchecked_hash for name in flags}


def test_update_drive_removes_a_module_and_its_bytecode_left_in_the_drive_app_by_an_earlier_update(tmp_path):
    drive = tmp_path / "drive"
    app = app_on(drive)
    app.mkdir(parents=True)
    stale = app / "stale.py"
    stale.write_text("")
    stale_pyc = Path(importlib.util.cache_from_source(str(stale)))
    stale_pyc.parent.mkdir()
    stale_pyc.write_bytes(b"")

    update_drive(drive)

    assert (stale.exists(), stale_pyc.exists()) == (False, False)


def test_update_drive_writes_the_repo_last_commit_as_short_hash_and_subject_to_the_drive_app_version(tmp_path):
    drive = empty_drive(tmp_path)

    update_drive(drive)

    last_commit = subprocess.run(
        ["git", "-C", str(REPO), "log", "-1", "--format=%h %s"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert version_on(drive).read_text().strip() == last_commit


def test_update_drive_writes_unknown_to_the_drive_app_version_when_git_log_fails(tmp_path):
    env = env_with_python313_on_path(tmp_path)
    failing_git = tmp_path / "bin" / "git"
    failing_git.write_text("#!/bin/sh\nexit 128\n")
    failing_git.chmod(0o755)
    drive = empty_drive(tmp_path)

    update_drive(drive, env=env)

    assert version_on(drive).read_text().strip() == "unknown"


def test_update_drive_copies_the_drive_scripts_into_the_drive_mediatagger_folder(tmp_path):
    drive = empty_drive(tmp_path)

    update_drive(drive)

    scripts = ["run.sh", "setup-pi.sh", "check-video-leak.sh"]
    on_drive = {
        name: copy.read_bytes() if copy.exists() else None
        for name in scripts
        for copy in [drive / "mediatagger" / name]
    }
    assert on_drive == {name: (UPDATE_DRIVE.parent / name).read_bytes() for name in scripts}


def write_files(files):
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def write_resource_forks(forks):
    write_files({fork: b"\x00\x05\x16\x07" for fork in forks})


def test_update_drive_deletes_macos_resource_fork_files_anywhere_under_the_drive_mediatagger_folder(tmp_path):
    drive = tmp_path / "drive"
    mediatagger = drive / "mediatagger"
    forks = [
        mediatagger / "._run.sh",
        mediatagger / "app" / "._VERSION",
        mediatagger / "logs" / "nested" / "._session.log",
    ]
    write_resource_forks(forks)

    update_drive(drive)

    assert [fork for fork in forks if fork.exists()] == []


def test_update_drive_leaves_macos_resource_fork_files_outside_the_drive_mediatagger_folder_in_place(tmp_path):
    drive = tmp_path / "drive"
    (drive / "mediatagger").mkdir(parents=True)
    forks = [
        drive / "._photo.jpg",
        drive / ".mediatagger" / "._tags.db",
        drive / "videos" / "nested" / "._clip.mov",
    ]
    write_resource_forks(forks)

    update_drive(drive)

    assert [fork for fork in forks if not fork.exists()] == []


def snapshot(root, folders):
    return {
        str(p.relative_to(root)): p.read_bytes() if p.is_file() else None
        for folder in folders
        for p in folder.rglob("*")
    }


def test_update_drive_leaves_the_drive_lib_and_debs_exactly_as_they_were(tmp_path):
    drive = tmp_path / "drive"
    mediatagger = drive / "mediatagger"
    files = {
        mediatagger / "lib-linux-aarch64-cp313" / "mpv.py": b"# mpv binding\n",
        mediatagger / "lib-linux-aarch64-cp313" / "__pycache__" / "mpv.cpython-313.pyc": b"\x00\x01bytecode",
        mediatagger / "lib-linux-aarch64-cp313" / "PIL" / "__init__.py": b"",
        mediatagger / "debs" / "libmpv2_0.39.0-3_arm64.deb": b"!<arch>\ndeb",
        mediatagger / "debs" / "Packages": b"Package: libmpv2\n",
    }
    write_files(files)
    (mediatagger / "debs" / "partial").mkdir()
    folders = [mediatagger / "lib-linux-aarch64-cp313", mediatagger / "debs"]
    before = snapshot(mediatagger, folders)

    update_drive(drive)

    assert snapshot(mediatagger, folders) == before


def test_update_drive_leaves_every_file_in_the_drive_tags_folder_byte_identical(tmp_path):
    drive = tmp_path / "drive"
    tags = drive / ".mediatagger"
    write_files({
        tags / "tags.db": b"SQLite format 3\x00tags",
        tags / "tags.db-wal": b"\x37\x7f\x06\x82wal",
        tags / "._tags.db": b"\x00\x05\x16\x07",
        tags / "thumbs" / "clip.mov.jpg": b"\xff\xd8\xff\xe0thumb",
    })
    before = snapshot(drive, [tags])

    update_drive(drive)

    assert snapshot(drive, [tags]) == before
