import os
import shutil
import subprocess
import sys
from pathlib import Path

from fakes import fake_command, recorded_args

RUN = Path(__file__).resolve().parent / "run.sh"


def drive_with_run_script(tmp_path):
    mediatagger = tmp_path / "drive" / "mediatagger"
    mediatagger.mkdir(parents=True)
    shutil.copy(RUN, mediatagger / "run.sh")
    return mediatagger


def env_with_fake_python3(tmp_path, script):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_command(bin_dir, "python3", script)
    env = {
        k: v for k, v in os.environ.items()
        if k not in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE")
    }
    return {**env, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}


def env_with_recording_python3(tmp_path, record):
    return env_with_fake_python3(tmp_path, f"printf '%s\\0' \"$@\" > \"{record}\"")


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


def test_run_starts_python3_with_pythondontwritebytecode_set_to_1(tmp_path):
    mediatagger = drive_with_run_script(tmp_path)
    record = tmp_path / "python3-dontwritebytecode"
    env = env_with_fake_python3(
        tmp_path, f"printf '%s' \"${{PYTHONDONTWRITEBYTECODE-unset}}\" > \"{record}\""
    )

    subprocess.run(["sh", str(mediatagger / "run.sh")], check=True, env=env)

    assert record.read_text() == "1"


REPO = RUN.parent.parent


def files_under(folder):
    return sorted(str(p.relative_to(folder)) for p in folder.rglob("*"))


def drive_laid_out_by_update_drive_with_the_locked_packages(tmp_path):
    drive = tmp_path / "drive"
    drive.mkdir()
    shims = tmp_path / "shims"
    shims.mkdir()
    (shims / "python3.13").symlink_to(sys._base_executable)
    subprocess.run(
        ["sh", str(REPO / "drive" / "update-drive.sh"), str(drive)], check=True,
        env={**os.environ, "PATH": f"{shims}{os.pathsep}{os.environ['PATH']}"},
    )
    requirements = tmp_path / "requirements.txt"
    subprocess.run(
        ["uv", "export", "--frozen", "--no-dev", "--no-hashes", "--no-emit-project",
         "--output-file", str(requirements)],
        check=True, cwd=REPO, capture_output=True,
    )
    subprocess.run(
        ["uv", "pip", "install", "--offline", "--python", sys._base_executable,
         "--target", str(drive / "mediatagger" / "lib-linux-aarch64-cp313"),
         "-r", str(requirements)],
        check=True, capture_output=True,
    )
    return drive.resolve()


def stderr_and_whether_still_running_after(seconds, command, **popen_kwargs):
    process = subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, **popen_kwargs,
    )
    try:
        _, log = process.communicate(timeout=seconds)
        return log, False
    except subprocess.TimeoutExpired:
        process.kill()
        _, log = process.communicate()
        return log, True


def test_run_with_a_real_python3_starts_the_real_app_from_the_drive_app_and_the_drive_gains_no_files(tmp_path):
    drive = drive_laid_out_by_update_drive_with_the_locked_packages(tmp_path)
    before = files_under(drive)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3").symlink_to(sys._base_executable)
    home = tmp_path / "home"
    home.mkdir()
    env = {
        **{k: v for k, v in os.environ.items() if not k.startswith("PYTHON") and k != "VIRTUAL_ENV"},
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "HOME": str(home), "XDG_DATA_HOME": str(home / "data"),
        "XDG_CONFIG_HOME": str(home / "config"), "XDG_CACHE_HOME": str(home / "cache"),
        "QT_QPA_PLATFORM": "offscreen", "PYTHONVERBOSE": "1",
    }

    log, still_running = stderr_and_whether_still_running_after(
        8, ["sh", str(drive / "mediatagger" / "run.sh")], env=env, cwd=home,
    )

    window = drive / "mediatagger" / "app" / "mediatagger" / "__pycache__" / "window.cpython-313.pyc"
    assert f"code object from '{window}'" in log
    assert still_running, log[-3000:]
    assert files_under(drive) == before
