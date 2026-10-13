import os
import shutil
import subprocess
from pathlib import Path

RUN = Path(__file__).resolve().parent / "run.sh"


def drive_with_run_script(tmp_path):
    mediatagger = tmp_path / "drive" / "mediatagger"
    mediatagger.mkdir(parents=True)
    shutil.copy(RUN, mediatagger / "run.sh")
    return mediatagger


def env_with_fake_python3(tmp_path, script):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3").write_text(f"#!/bin/sh\n{script}\n")
    (bin_dir / "python3").chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return {**env, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}


def env_with_recording_python3(tmp_path, record):
    return env_with_fake_python3(tmp_path, f"printf '%s\\0' \"$@\" > \"{record}\"")


def recorded_args(record):
    return record.read_bytes().split(b"\0")[:-1] if record.exists() else None


def test_run_starts_python3_importing_mediatagger_main_with_its_arguments_passed_through_unchanged(tmp_path):
    mediatagger = drive_with_run_script(tmp_path)
    record = tmp_path / "python3-args"
    env = env_with_recording_python3(tmp_path, record)

    subprocess.run(
        ["sh", str(mediatagger / "run.sh"), "/media/My Videos", "two  spaces", ""],
        check=True, env=env,
    )

    assert recorded_args(record) == [
        b"-c", b"import mediatagger; mediatagger.main()",
        b"/media/My Videos", b"two  spaces", b"",
    ]


def test_run_from_any_working_directory_gives_python3_a_pythonpath_of_its_own_app_then_lib_folders(tmp_path):
    mediatagger = drive_with_run_script(tmp_path).resolve()
    record = tmp_path / "python3-pythonpath"
    env = env_with_fake_python3(tmp_path, f"printf '%s' \"$PYTHONPATH\" > \"{record}\"")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    subprocess.run(
        ["sh", os.path.relpath(mediatagger / "run.sh", elsewhere)],
        check=True, env=env, cwd=elsewhere,
    )

    assert record.read_text() == f"{mediatagger}/app:{mediatagger}/lib-linux-aarch64-cp313"
