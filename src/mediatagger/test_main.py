import subprocess
import sys
from pathlib import Path

from PySide6.QtGui import QColor

from mediatagger.test_viewer import make_image, offscreen_environment, run_python_offscreen, shown_launch_viewer, shown_texts, shown_viewer_on
from mediatagger.test_viewer_open import drive_without_a_tag_library_holding_one_image
from mediatagger.viewer import DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT

RUN_MEDIATAGGER_COMMAND = (
    "from importlib.metadata import entry_points\n"
    "(command,) = entry_points(group='console_scripts', name='mediatagger')\n"
    "command.load()()\n"
)

REPORT_SHOWN_WINDOW_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.test_viewer import centre_colour\n"
    "app = QApplication([])\n"
    "def report():\n"
    "    for window in QApplication.topLevelWidgets():\n"
    "        if window.isVisible():\n"
    "            print(f'fullscreen={window.isFullScreen()} centre={centre_colour(window).name()}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, report)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND


def test_running_the_mediatagger_command_on_a_folder_opens_the_fullscreen_viewer_on_its_first_item(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    result = run_python_offscreen(REPORT_SHOWN_WINDOW_SCRIPT, str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"fullscreen=True centre={QColor('red').name()}"


def test_the_installed_mediatagger_executable_started_on_its_own_keeps_running_with_its_viewer_open(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    executable = Path(sys.executable).parent / "mediatagger"
    process = subprocess.Popen(
        [str(executable), str(tmp_path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=offscreen_environment(),
    )
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    still_running = process.poll() is None
    process.kill()
    _, stderr = process.communicate()
    assert still_running, stderr


def test_running_the_mediatagger_command_on_a_file_opens_the_fullscreen_viewer_on_that_file(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    make_image(tmp_path / "IMG_3.png", "green")
    result = run_python_offscreen(REPORT_SHOWN_WINDOW_SCRIPT, str(tmp_path / "IMG_2.png"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"fullscreen=True centre={QColor('blue').name()}"

PRESS_ESC_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication\n"
    "app = QApplication([])\n"
    "def press_esc():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    QTest.keyClick(window, Qt.Key.Key_Escape)\n"
    "QTimer.singleShot(1000, press_esc)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND + "print('exited', flush=True)\n"


def test_pressing_esc_in_the_mediatagger_command_makes_it_exit_cleanly(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    result = run_python_offscreen(PRESS_ESC_SCRIPT, str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "exited"

REPORT_SHOWN_TEXTS_ON_TIMER = (
    "import sys\n"
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.test_viewer import shown_texts\n"
    "app = QApplication([])\n"
    "def report():\n"
    "    for window in QApplication.topLevelWidgets():\n"
    "        if window.isVisible():\n"
    "            for text in shown_texts(window):\n"
    "                print(text, flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, report)\n"
)

REPORT_SHOWN_TEXTS_WITH_NO_PATH_SCRIPT = (
    REPORT_SHOWN_TEXTS_ON_TIMER
    + "sys.argv = ['mediatagger']\n"
    + RUN_MEDIATAGGER_COMMAND
)


def test_running_the_mediatagger_command_with_no_path_opens_the_window_showing_the_launch_text(qtbot):
    launch_texts = shown_texts(shown_launch_viewer(qtbot))
    result = run_python_offscreen(REPORT_SHOWN_TEXTS_WITH_NO_PATH_SCRIPT)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == launch_texts

DROP_FOLDER_WITH_NO_PATH_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.test_viewer import centre_colour, shown_texts\n"
    "from mediatagger.test_viewer_open import drag_and_drop_onto\n"
    "app = QApplication([])\n"
    "folder = sys.argv[1]\n"
    "def drop_then_report():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    drag_and_drop_onto(window, folder)\n"
    "    colour = centre_colour(window).name()\n"
    "    texts = shown_texts(window)\n"
    "    print(f'centre={colour} texts={texts}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, drop_then_report)\n"
    "sys.argv = ['mediatagger']\n"
) + RUN_MEDIATAGGER_COMMAND


def test_dropping_a_folder_onto_the_mediatagger_command_started_with_no_path_starts_its_slideshow_at_its_first_item(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    result = run_python_offscreen(DROP_FOLDER_WITH_NO_PATH_SCRIPT, str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"centre={QColor('red').name()} texts=[]"

REPORT_SHOWN_TEXTS_SCRIPT = (
    REPORT_SHOWN_TEXTS_ON_TIMER
    + "sys.argv = ['mediatagger', sys.argv[1]]\n"
    + RUN_MEDIATAGGER_COMMAND
)


def test_running_the_mediatagger_command_on_a_path_that_does_not_exist_keeps_running_and_says_it_cant_open_it(qtbot):
    missing = Path("/no/such/path")
    cant_open_texts = shown_texts(shown_viewer_on(qtbot, missing))
    result = run_python_offscreen(REPORT_SHOWN_TEXTS_SCRIPT, str(missing))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == cant_open_texts

DECLINE_CREATING_A_LIBRARY_SCRIPT = (
    "import os, sys\n"
    "drive = sys.argv[1]\n"
    "os.path.ismount = lambda path: os.fspath(path) == drive\n"
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.test_viewer import centre_colour\n"
    "from mediatagger.test_viewer_open import status_bar_texts\n"
    "app = QApplication([])\n"
    "asked = []\n"
    "def decline():\n"
    "    question = QApplication.activeModalWidget()\n"
    "    asked.append(question is not None)\n"
    "    if question is not None:\n"
    "        question.reject()\n"
    "def report():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    print(f'asked={asked} centre={centre_colour(window).name()} status={status_bar_texts(window)}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(500, decline)\n"
    "QTimer.singleShot(1500, report)\n"
    "sys.argv = ['mediatagger', sys.argv[2]]\n"
) + RUN_MEDIATAGGER_COMMAND


def test_running_the_mediatagger_command_on_a_drive_without_a_tag_library_asks_and_declining_keeps_the_slideshow_saying_the_drive_has_no_tag_library(tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    result = run_python_offscreen(DECLINE_CREATING_A_LIBRARY_SCRIPT, str(drive), str(folder))
    assert result.returncode == 0, result.stderr
    no_library_status = [DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT.format(drive.name)]
    assert result.stdout.strip() == f"asked=[True] centre={QColor('red').name()} status={no_library_status}"
