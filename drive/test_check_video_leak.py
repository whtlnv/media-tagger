import os
import re
import shutil
import subprocess
from pathlib import Path

from fakes import recorded_args

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


def test_check_video_leak_logs_under_home_and_copies_the_logs_to_the_drive_results_only_after_the_app_has_exited(tmp_path):
    mediatagger = drive_with_check_script(tmp_path)
    results = tmp_path / "drive" / "results"
    seen_while_running = tmp_path / "results-seen-while-running"
    write_executable(
        mediatagger / "run.sh",
        f"ls -A \"{results}\" > \"{seen_while_running}\" 2>/dev/null; echo app output; echo app error >&2",
    )
    env = env_with_fake_tools(tmp_path)

    subprocess.run(
        ["sh", str(mediatagger / "check-video-leak.sh"), "/media/clip.mp4"],
        check=True, env=env, timeout=30,
    )

    [log] = (Path(env["HOME"]) / "mediatagger-check").iterdir()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d{6}", log.name)
    logged = {f.name: f.read_bytes() for f in log.iterdir()}
    assert {"info.txt", "fds.txt", "app.log"} <= logged.keys()
    assert b"abc1234 subject" in logged["info.txt"] and b"/media/clip.mp4" in logged["info.txt"]
    assert b"app output" in logged["app.log"] and b"app error" in logged["app.log"]
    copied = results / f"check-video-leak-{log.name}"
    assert {f.name: f.read_bytes() for f in copied.iterdir()} == logged
    assert seen_while_running.read_text() == ""
