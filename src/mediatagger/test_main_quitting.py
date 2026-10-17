import os
import subprocess
import sys
import time

from mediatagger.test_main import DEFINE_SHOWN_WINDOW, DEFINE_SHOWN_WINDOW_AND_ITS_PAGE, RUN_MEDIATAGGER_COMMAND, SILENCE_THE_VIEWERS_ENGINE
from mediatagger.test_video import make_clip
from mediatagger.test_viewer import make_image, offscreen_environment
from mediatagger.test_viewer_backup import tags_in_newest_backup
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image

PRESS_ESC_THEN_SAY_QUITTING_THEN_ESC_IN_THE_GRID_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication\n"
    "app = QApplication([])\n"
) + DEFINE_SHOWN_WINDOW + (
    "def quit_from_the_grid():\n"
    "    print('quitting', flush=True)\n"
    "    QTest.keyClick(shown_window(), Qt.Key.Key_Escape)\n"
    "def press_esc_then_quit_while_thumbnails_generate():\n"
    "    QTest.keyClick(shown_window(), Qt.Key.Key_Escape)\n"
    "    QTimer.singleShot(1000, quit_from_the_grid)\n"
    "QTimer.singleShot(1000, press_esc_then_quit_while_thumbnails_generate)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND


def run_python_then_time_from_quitting_to_ending(script, argument, environment):
    process = subprocess.Popen(
        [sys.executable, "-c", script, argument],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment,
    )
    try:
        assert process.stdout.readline().strip() == "quitting"
        quit_at = time.monotonic()
        process.wait(timeout=30)
        seconds_to_end = time.monotonic() - quit_at
    finally:
        process.kill()
        _, stderr = process.communicate()
    return process.returncode, seconds_to_end, stderr


def offscreen_environment_with_slow_fake_video_tools_in(folder):
    folder.mkdir()
    for tool, output in [("ffprobe", "echo 10.0"), ("ffmpeg", "true")]:
        script = folder / tool
        script.write_text(f"#!/bin/sh\nsleep 0.5\n{output}\n")
        script.chmod(0o755)
    environment = offscreen_environment()
    environment["PATH"] = f"{folder}{os.pathsep}{environment['PATH']}"
    return environment


def put_60_empty_videos_in(folder):
    for number in range(60):
        (folder / f"VID_{number:02}.mp4").write_bytes(b"")


def test_pressing_esc_to_quit_the_mediatagger_command_from_a_grid_whose_thumbnails_are_still_generating_ends_the_process_within_3_s(tmp_path):
    folder = tmp_path / "videos"
    folder.mkdir()
    make_image(folder / "A.png", "red")
    put_60_empty_videos_in(folder)
    environment = offscreen_environment_with_slow_fake_video_tools_in(tmp_path / "bin")
    returncode, seconds_to_end, stderr = run_python_then_time_from_quitting_to_ending(PRESS_ESC_THEN_SAY_QUITTING_THEN_ESC_IN_THE_GRID_SCRIPT, str(folder), environment)
    assert returncode == 0, stderr
    assert seconds_to_end < 3, stderr

SAY_QUITTING_THEN_CLOSE_THE_WINDOW_WHILE_THE_VIDEO_PLAYS_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
) + SILENCE_THE_VIEWERS_ENGINE + (
    "from mediatagger.test_viewer import make_surface_ready\n"
    "app = QApplication([])\n"
) + DEFINE_SHOWN_WINDOW_AND_ITS_PAGE + (
    "def stand_in_for_the_video_surface_becoming_ready():\n"
    "    window, viewer = shown()\n"
    "    make_surface_ready(viewer)\n"
    "    QTimer.singleShot(1500, quit_while_the_video_plays)\n"
    "def quit_while_the_video_plays():\n"
    "    window, viewer = shown()\n"
    "    viewer.video_player.engine.wait_for_property('time-pos', lambda pos: pos is not None and pos > 0, timeout=5)\n"
    "    print('quitting', flush=True)\n"
    "    window.close()\n"
    "QTimer.singleShot(1000, stand_in_for_the_video_surface_becoming_ready)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND


def test_quitting_the_mediatagger_command_while_a_video_plays_ends_the_process_within_3_s(tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    returncode, seconds_to_end, stderr = run_python_then_time_from_quitting_to_ending(SAY_QUITTING_THEN_CLOSE_THE_WINDOW_WHILE_THE_VIDEO_PLAYS_SCRIPT, str(clip), offscreen_environment())
    assert returncode == 0, stderr
    assert seconds_to_end < 3, stderr

ENTER_A_TAG_THEN_ESC_THEN_SAY_QUITTING_THEN_ESC_IN_THE_GRID_ON_A_DRIVE_SCRIPT = (
    "import os, sys\n"
    "drive = os.path.dirname(sys.argv[1])\n"
    "os.path.ismount = lambda path: os.fspath(path) == drive\n"
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication\n"
    "app = QApplication([])\n"
) + DEFINE_SHOWN_WINDOW + (
    "def quit_from_the_grid():\n"
    "    print('quitting', flush=True)\n"
    "    QTest.keyClick(shown_window(), Qt.Key.Key_Escape)\n"
    "def enter_a_tag_then_esc_then_quit_while_thumbnails_generate():\n"
    "    window = shown_window()\n"
    "    QTest.keyClick(window, Qt.Key.Key_T)\n"
    "    QTest.keyClicks(window.focusWidget(), 'beach')\n"
    "    QTest.keyClick(window.focusWidget(), Qt.Key.Key_Return)\n"
    "    QTest.keyClick(window, Qt.Key.Key_Escape)\n"
    "    QTimer.singleShot(1000, quit_from_the_grid)\n"
    "QTimer.singleShot(1000, enter_a_tag_then_esc_then_quit_while_thumbnails_generate)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND


def test_quitting_the_mediatagger_command_with_a_library_whose_backup_is_due_ends_the_process_within_3_s(tmp_path, monkeypatch):
    data_home = tmp_path / "data-home"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    put_60_empty_videos_in(folder)
    environment = offscreen_environment_with_slow_fake_video_tools_in(tmp_path / "bin")
    returncode, seconds_to_end, stderr = run_python_then_time_from_quitting_to_ending(ENTER_A_TAG_THEN_ESC_THEN_SAY_QUITTING_THEN_ESC_IN_THE_GRID_ON_A_DRIVE_SCRIPT, str(folder), environment)
    assert returncode == 0, stderr
    assert seconds_to_end < 3, stderr
    backup_root = data_home / "mediatagger" / "backups"
    assert tags_in_newest_backup(backup_root, drive, tmp_path / "restored", folder.relative_to(drive) / "IMG_1.png") == ["beach"]
