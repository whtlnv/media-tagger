from PySide6.QtCore import QPoint, QRect

_WHEEL_NOTCH = 120  # angleDelta units per mouse-wheel notch
_ZOOM_STEP = 1.25
_MAX_ZOOM = 3  # times the fitted size


class Zoom:
    """How far the viewer's picture is zoomed in from its fitted size: 1 is fitted."""

    def __init__(self):
        self.level = 1

    def wheel(self, angle_delta):
        """Turn the mouse wheel by angle_delta (eighths of a degree; positive is up, which zooms in)."""
        self.level = min(_MAX_ZOOM, max(1, self.level * _ZOOM_STEP ** (angle_delta / _WHEEL_NOTCH)))

    def shown(self, fitted):
        """Where the picture fitted at fitted is shown at this zoom."""
        target = QRect(QPoint(), fitted.size() * self.level)
        target.moveCenter(fitted.center())
        return target
