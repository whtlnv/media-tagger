from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QLabel


class ProgressBar(QLabel):
    """A video's progress, shown only while the video surface it follows is shown."""

    def __init__(self, parent):
        super().__init__(parent)
        self.hide()

    def follow(self, surface):
        surface.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Hide and watched.isHidden():  # the surface itself, not a hidden ancestor
            self.hide()
        return False

    def start(self, seconds):
        minutes, seconds = divmod(round(seconds), 60)
        self.setText(f"0:00 / {minutes}:{seconds:02d}")
        self.show()
