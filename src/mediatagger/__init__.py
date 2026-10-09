import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


def main() -> None:
    from mediatagger.viewer import Viewer

    app = QApplication.instance() or QApplication(sys.argv)
    viewer = Viewer(Path(sys.argv[1]))
    viewer.show()
    app.exec()
