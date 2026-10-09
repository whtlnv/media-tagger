import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


def main() -> None:
    from mediatagger.viewer import Viewer

    viewer = Viewer(Path(sys.argv[1]))
    viewer.show()
    QApplication.exec()
