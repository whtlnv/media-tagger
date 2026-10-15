from PySide6.QtCore import QPoint, QPointF, QRect

_WHEEL_NOTCH = 120  # angleDelta units per mouse-wheel notch
_ZOOM_STEP = 1.25
_MAX_ZOOM = 3  # times the fitted size


class Zoom:
    """How far the viewer's picture is zoomed in from its fitted size: 1 is fitted."""

    def __init__(self):
        self.level = 1
        self.centre = QPointF()  # of the shown picture, from the fitted picture's centre

    def wheel(self, angle_delta, at):
        """Turn the mouse wheel by angle_delta (eighths of a degree; positive is up, which zooms in) with the mouse
        at at, from the fitted picture's centre: the picture point under the mouse stays under it."""
        zoomed = self.level * _ZOOM_STEP ** (angle_delta / _WHEEL_NOTCH)
        level = min(_MAX_ZOOM, max(1, zoomed))
        self.centre = at - (at - self.centre) * (level / self.level) if level > 1 else QPointF()
        self.level = level

    def shown(self, fitted):
        """Where the picture fitted at fitted is shown at this zoom."""
        target = QRect(QPoint(), fitted.size() * self.level)
        target.moveCenter(fitted.center() + self.centre.toPoint())
        return target
