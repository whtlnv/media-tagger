import subprocess
import sys
from pathlib import Path

from PySide6.QtGui import QColor

from mediatagger.test_viewer import make_image, offscreen_environment, run_python_offscreen

REPORT_SHOWN_WINDOW_SCRIPT = (
    "import sys\n"
    "from importlib.metadata import entry_points\n"
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "app = QApplication([])\n"
    "def report():\n"
    "    for window in QApplication.topLevelWidgets():\n"
    "        if window.isVisible():\n"
    "            frame = window.grab().toImage()\n"
    "            colour = frame.pixelColor(frame.width() // 2, frame.height() // 2).name()\n"
    "            print(f'fullscreen={window.isFullScreen()} centre={colour}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, report)\n"
    "(command,) = entry_points(group='console_scripts', name='mediatagger')\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
    "command.load()()\n"
)


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
    "from importlib.metadata import entry_points\n"
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication\n"
    "app = QApplication([])\n"
    "def press_esc():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    QTest.keyClick(window, Qt.Key.Key_Escape)\n"
    "QTimer.singleShot(1000, press_esc)\n"
    "(command,) = entry_points(group='console_scripts', name='mediatagger')\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
    "command.load()()\n"
    "print('exited', flush=True)\n"
)


def test_pressing_esc_in_the_mediatagger_command_makes_it_exit_cleanly(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    result = run_python_offscreen(PRESS_ESC_SCRIPT, str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "exited"
