import subprocess
import sys

import pytest

from mediatagger.test_main import RUN_MEDIATAGGER_COMMAND
from mediatagger.test_viewer import offscreen_environment


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


@pytest.mark.parametrize(("category_name", "logging_rules", "expected"), [
    pytest.param("qt.qpa.wayland.textinput", {}, "warnings=False", id="starts with wayland textinput warnings disabled"),
    pytest.param("qt.qpa.wayland", {}, "warnings=True", id="leaves wayland warnings enabled"),
    pytest.param(
        "qt.qpa.wayland.textinput", {"QT_LOGGING_RULES": "qt.qpa.wayland.textinput=true"}, "warnings=True",
        id="started with textinput warnings enabled in QT_LOGGING_RULES keeps them enabled",
    ),
])
def test_the_mediatagger_command_disables_only_wayland_textinput_warnings_unless_qt_logging_rules_enables_them(category_name, logging_rules, expected):
    result = subprocess.run(
        [sys.executable, "-c", script_reporting_whether_the_mediatagger_command_enables_warnings_for(category_name)],
        capture_output=True, text=True, timeout=30,
        env={**offscreen_environment(), **logging_rules},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected
