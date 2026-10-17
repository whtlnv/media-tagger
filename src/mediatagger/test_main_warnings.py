import subprocess
import sys

from mediatagger.test_main import RUN_MEDIATAGGER_COMMAND
from mediatagger.test_viewer import offscreen_environment, run_python_offscreen


def script_reporting_whether_the_mediatagger_command_enables_warnings_for(category_name):
    return (
        "import sys\n"
        "from PySide6.QtCore import QLoggingCategory, QTimer\n"
        "from PySide6.QtWidgets import QApplication\n"
        "app = QApplication([])\n"
        "def report():\n"
        f"    category = QLoggingCategory('{category_name}')\n"
        "    print(f'warnings={category.isWarningEnabled()}', flush=True)\n"
        "    QApplication.closeAllWindows()\n"
        "    QApplication.quit()\n"
        "QTimer.singleShot(1000, report)\n"
        "sys.argv = ['mediatagger']\n"
    ) + RUN_MEDIATAGGER_COMMAND


def test_the_mediatagger_command_starts_with_wayland_textinput_warnings_disabled():
    result = run_python_offscreen(script_reporting_whether_the_mediatagger_command_enables_warnings_for("qt.qpa.wayland.textinput"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "warnings=False"


def test_the_mediatagger_command_leaves_wayland_warnings_enabled():
    result = run_python_offscreen(script_reporting_whether_the_mediatagger_command_enables_warnings_for("qt.qpa.wayland"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "warnings=True"


def test_the_mediatagger_command_started_with_textinput_warnings_enabled_in_qt_logging_rules_keeps_them_enabled():
    result = subprocess.run(
        [sys.executable, "-c", script_reporting_whether_the_mediatagger_command_enables_warnings_for("qt.qpa.wayland.textinput")],
        capture_output=True, text=True, timeout=30,
        env={**offscreen_environment(), "QT_LOGGING_RULES": "qt.qpa.wayland.textinput=true"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "warnings=True"
