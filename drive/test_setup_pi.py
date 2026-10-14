import os
import shutil
import subprocess
from pathlib import Path

SETUP_PI = Path(__file__).resolve().parent / "setup-pi.sh"


def drive_with_setup_pi(tmp_path):
    mediatagger = (tmp_path / "drive" / "mediatagger").resolve()
    (mediatagger / "debs").mkdir(parents=True)
    shutil.copy(SETUP_PI, mediatagger / "setup-pi.sh")
    return mediatagger


def fake_command(bin_dir, name, script):
    (bin_dir / name).write_text(f"#!/bin/sh\n{script}\n")
    (bin_dir / name).chmod(0o755)


def fake_bin_env(tmp_path, bin_dir, **extra):
    """An environment whose commands come from bin_dir first and whose home and data folders are under tmp_path."""
    (tmp_path / "tmp").mkdir()
    (tmp_path / "home").mkdir(exist_ok=True)
    return {
        **{k: v for k, v in os.environ.items() if k not in ("FAKE_SUDO", "XDG_DATA_HOME")},
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "TMPDIR": str(tmp_path / "tmp"),
        "HOME": str(tmp_path / "home"),
        "XDG_DATA_HOME": str(tmp_path / "home" / "share"),
        **extra,
    }


def fake_recording_apt_get(bin_dir, record):
    fake_command(bin_dir, "apt-get", f"""
i=1; while [ -e "{record}/$i" ]; do i=$((i+1)); done
mkdir "{record}/$i"
printf '%s\\0' "$@" > "{record}/$i/args"
printf '%s' "${{FAKE_SUDO-no}}" > "{record}/$i/via-sudo"
for a; do
  case "$a" in Dir::Etc::sourcelist=*) cp "${{a#Dir::Etc::sourcelist=}}" "{record}/$i/sourcelist";; esac
done""")


def apt_get_calls(record):
    calls = []
    for call in sorted(record.iterdir(), key=lambda d: int(d.name)):
        args = (call / "args").read_bytes().split(b"\0")[:-1]
        sourcelist = call / "sourcelist"
        calls.append({
            "via_sudo": (call / "via-sudo").read_text() == "yes",
            "args": [a.decode() for a in args],
            "sourcelist": sourcelist.read_text() if sourcelist.exists() else None,
        })
    return calls


def split_apt_options(args):
    options, rest = {}, []
    it = iter(args)
    for a in it:
        if a == "-o":
            key, _, value = next(it).partition("=")
            options[key] = value
        else:
            rest.append(a)
    return options, rest


def test_setup_pi_without_libmpv2_installs_it_with_sudo_apt_get_from_a_temporary_trusted_source_on_the_drives_debs(tmp_path):
    mediatagger = drive_with_setup_pi(tmp_path)
    record = tmp_path / "apt-get-calls"
    record.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_command(bin_dir, "dpkg-query", "exit 1")
    fake_command(bin_dir, "sudo", 'FAKE_SUDO=yes exec "$@"')
    fake_recording_apt_get(bin_dir, record)
    env = fake_bin_env(tmp_path, bin_dir)

    subprocess.run(["sh", str(mediatagger / "setup-pi.sh")], check=True, env=env)

    calls = apt_get_calls(record)
    assert [split_apt_options(c["args"])[1] for c in calls] == [
        ["update"],
        ["install", "-y", "--no-install-recommends", "libmpv2"],
    ]
    assert all(c["via_sudo"] for c in calls)
    assert all(c["sourcelist"] == f"deb [trusted=yes] file:{mediatagger}/debs ./\n" for c in calls)
    options = [split_apt_options(c["args"])[0] for c in calls]
    assert all(o["Dir::Etc::sourceparts"] == "-" for o in options)
    lists_dirs = {o["Dir::State::Lists"] for o in options}
    assert len(lists_dirs) == 1 and lists_dirs != {"/var/lib/apt/lists"}


def test_setup_pi_with_libmpv2_already_installed_runs_neither_sudo_nor_apt_get(tmp_path):
    mediatagger = drive_with_setup_pi(tmp_path)
    record = tmp_path / "apt-get-calls"
    record.mkdir()
    sudo_ran = tmp_path / "sudo-ran"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_command(bin_dir, "dpkg-query", "printf 'install ok installed'")
    fake_command(bin_dir, "sudo", f'touch "{sudo_ran}"; exec "$@"')
    fake_recording_apt_get(bin_dir, record)
    env = fake_bin_env(tmp_path, bin_dir)

    subprocess.run(["sh", str(mediatagger / "setup-pi.sh")], check=True, env=env)

    assert not sudo_ran.exists()
    assert apt_get_calls(record) == []


def test_setup_pi_removes_its_temporary_apt_lists_folder_after_installing_libmpv2(tmp_path):
    mediatagger = drive_with_setup_pi(tmp_path)
    lists_record = tmp_path / "lists-dir"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_command(bin_dir, "dpkg-query", "exit 1")
    fake_command(bin_dir, "sudo", 'exec "$@"')
    fake_command(bin_dir, "apt-get", f"""
for a; do
  case "$a" in Dir::State::Lists=*) d="${{a#Dir::State::Lists=}}"; mkdir -p "$d/partial"; printf '%s' "$d" > "{lists_record}";; esac
done""")
    env = fake_bin_env(tmp_path, bin_dir)

    subprocess.run(["sh", str(mediatagger / "setup-pi.sh")], check=True, env=env)

    assert not Path(lists_record.read_text()).exists()


def test_setup_pi_writes_a_mediatagger_desktop_entry_that_launches_the_drives_run_sh(tmp_path):
    mediatagger = drive_with_setup_pi(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_command(bin_dir, "dpkg-query", "printf 'install ok installed'")
    env = fake_bin_env(tmp_path, bin_dir)

    subprocess.run(["sh", str(mediatagger / "setup-pi.sh")], check=True, env=env)

    desktop = Path(env["XDG_DATA_HOME"]) / "applications" / "mediatagger.desktop"
    assert desktop.is_file()
    lines = desktop.read_text().splitlines()
    assert lines[0] == "[Desktop Entry]"
    assert {
        "Type=Application",
        "Name=MediaTagger",
        f'Exec=sh "{mediatagger}/run.sh"',
        "Terminal=false",
        "Categories=AudioVideo;Video;Graphics;",
    } <= set(lines[1:])


def test_setup_pi_without_xdg_data_home_writes_the_desktop_entry_under_home_local_share(tmp_path):
    mediatagger = drive_with_setup_pi(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_command(bin_dir, "dpkg-query", "printf 'install ok installed'")
    env = fake_bin_env(tmp_path, bin_dir)
    del env["XDG_DATA_HOME"]

    subprocess.run(["sh", str(mediatagger / "setup-pi.sh")], check=True, env=env)

    desktop = Path(env["HOME"]) / ".local" / "share" / "applications" / "mediatagger.desktop"
    assert desktop.is_file()
