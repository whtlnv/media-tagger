import os
import subprocess
import sys

from PySide6.QtGui import QColor

from mediatagger.test_viewer import make_image


def test_running_the_mediatagger_command_on_a_folder_opens_the_fullscreen_viewer_on_its_first_item(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    script = (
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
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        capture_output=True, text=True, timeout=30,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"fullscreen=True centre={QColor('red').name()}"
