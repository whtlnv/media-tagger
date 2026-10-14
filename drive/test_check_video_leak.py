import os
import shutil
import subprocess
from pathlib import Path

CHECK_VIDEO_LEAK = Path(__file__).resolve().parent / "check-video-leak.sh"


def write_executable(path, script):
    path.write_text(f"#!/bin/sh\n{script}\n")
    path.chmod(0o755)


def drive_with_check_script(tmp_path):
    mediatagger = tmp_path / "drive" / "mediatagger"
    (mediatagger / "app").mkdir(parents=True)
    (mediatagger / "app" / "VERSION").write_text("abc1234 subject\n")
    shutil.copy(CHECK_VIDEO_LEAK, mediatagger / "check-video-leak.sh")
    return mediatagger


def env_with_fake_tools(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    write_executable(bin_dir / "sleep", "exit 0")
    write_executable(bin_dir / "dpkg-query", "exit 1")
    write_executable(bin_dir / "pgrep", "exit 1")
    home = tmp_path / "home"
    home.mkdir()
    return {**os.environ, "HOME": str(home), "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}


def recorded_args(record):
    return record.read_bytes().split(b"\0")[:-1] if record.exists() else None


def test_check_video_leak_starts_the_app_on_its_target_through_the_drives_run_sh(tmp_path):
    mediatagger = drive_with_check_script(tmp_path)
    record = tmp_path / "run-sh-args"
    write_executable(mediatagger / "run.sh", f"printf '%s\\0' \"$@\" > \"{record}\"")
    env = env_with_fake_tools(tmp_path)

    subprocess.run(
        ["sh", str(mediatagger / "check-video-leak.sh"), "/media/My Videos/clip.mp4"],
        check=True, env=env, timeout=30,
    )

    assert recorded_args(record) == [b"/media/My Videos/clip.mp4"]
