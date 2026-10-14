import sys
from pathlib import Path

from PySide6.QtCore import QLoggingCategory
from PySide6.QtWidgets import QApplication


def main() -> None:
    from mediatagger.window import Window

    QLoggingCategory.setFilterRules("qt.qpa.wayland.textinput.warning=false")
    app = QApplication.instance() or QApplication(sys.argv)
    window = Window(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    window.show()
    app.exec()
