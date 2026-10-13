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


def env_with_recording_python3(tmp_path, record):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3").write_text(f"#!/bin/sh\nprintf '%s\\0' \"$@\" > \"{record}\"\n")
    (bin_dir / "python3").chmod(0o755)
    return {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}


def test_run_starts_python3_importing_mediatagger_main_with_its_arguments_passed_through_unchanged(tmp_path):
    mediatagger = drive_with_run_script(tmp_path)
    record = tmp_path / "python3-args"
    env = env_with_recording_python3(tmp_path, record)

    subprocess.run(
        ["sh", str(mediatagger / "run.sh"), "/media/My Videos", "two  spaces", ""],
        check=True, env=env,
    )

    args = record.read_bytes().split(b"\0")[:-1] if record.exists() else None
    assert args == [
        b"-c", b"import mediatagger; mediatagger.main()",
        b"/media/My Videos", b"two  spaces", b"",
    ]
