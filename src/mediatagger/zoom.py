from PySide6.QtCore import QPointF, QRectF

_WHEEL_NOTCH = 120  # angleDelta units per mouse-wheel notch
_ZOOM_STEP = 0.1  # of the fitted size per notch
_MAX_ZOOM = 3  # times the fitted size


class Zoom:
    """How far the viewer's picture is zoomed in from its fitted size (level 1 is fitted, 3 the most) and where it is
    panned: pan is the shown picture's centre from the window's centre, in fractions of the shown picture's size —
    the units of mpv's video-pan-x/y, so a video can be zoomed the same way."""

    def __init__(self):
        self.level = 1
        self.pan = QPointF()

    def shown(self, fitted, window):
        """Where the picture, fitted to window at fitted, is shown at this zoom."""
        shown = QRectF(QPointF(), fitted.size().toSizeF() * self.level)
        shown.moveCenter(QRectF(window).center() + QPointF(self.pan.x() * shown.width(), self.pan.y() * shown.height()))
        return shown

    def detail(self):
        """How many times the window's size a picture must be decoded at to stay sharp at this zoom: fitted needs no
        more than the window; once zoomed in, enough for the closest zoom, so zooming further needs no new decode."""
        return _MAX_ZOOM if self.level > 1 else 1

    def wheel(self, angle_delta, at, fitted, window):
        """Turn the mouse wheel by angle_delta (eighths of a degree; positive is up, which zooms in) with the mouse at at:
        the picture point under the mouse stays under it, unless that would leave black between the picture and a window
        edge — a picture bigger than the window always covers it, a smaller one lies inside it."""
        before = self.shown(fitted, window)
        level = min(_MAX_ZOOM, max(1, self.level + _ZOOM_STEP * angle_delta / _WHEEL_NOTCH))
        if level == 1:
            self.level, self.pan = 1, QPointF()
            return
        scale = level / self.level
        at = QPointF(at)
        after = QRectF(at + (before.topLeft() - at) * scale, before.size() * scale)
        window = QRectF(window)
        after.moveLeft(_within(after.left(), window.left(), window.right() - after.width()))
        after.moveTop(_within(after.top(), window.top(), window.bottom() - after.height()))
        offset = after.center() - window.center()
        self.level, self.pan = level, QPointF(offset.x() / after.width(), offset.y() / after.height())


def _within(edge, first, last):
    """edge kept between first and last, whichever way round they are."""
    return min(max(first, last), max(min(first, last), edge))
