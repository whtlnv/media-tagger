from PySide6.QtWidgets import QLabel


class ProgressBar(QLabel):
    def show_length(self, seconds):
        minutes, seconds = divmod(round(seconds), 60)
        self.setText(f"0:00 / {minutes}:{seconds:02d}")
