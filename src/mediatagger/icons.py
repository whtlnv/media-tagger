"""Small icons painted with shapes, never with a font: the Pi's fonts (DejaVu) have no emoji, so an emoji symbol shows
there as an empty square."""

from enum import StrEnum
from functools import lru_cache

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath

ICON_KEY = "icon"  # an icon's image carries its name under this key


class Icon(StrEnum):
    TAG = "<tag>"


def draw_icon(painter, rect, icon, color):
    """Paints the icon to fill the square rect, in color."""
    ratio = painter.device().devicePixelRatioF()
    painter.drawImage(rect, icon_image(icon, rect.height(), QColor(color).rgba(), ratio))


@lru_cache(maxsize=64)
def icon_image(icon, side, rgba, ratio=1.0):
    """The icon painted once on a transparent square of side pixels (times the screen's ratio), kept for every tile
    that shows it at that size and colour."""
    image = QImage(round(side * ratio), round(side * ratio), QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    image.setText(ICON_KEY, icon)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor.fromRgba(rgba))
    painter.drawPath(_tag(image.height()))
    painter.end()
    image.setDevicePixelRatio(ratio)
    return image


def _tag(s):
    """A luggage tag pointing left, with its hole."""
    tag = QPainterPath()
    tag.moveTo(0.05 * s, 0.5 * s)
    tag.lineTo(0.38 * s, 0.17 * s)
    tag.lineTo(0.95 * s, 0.17 * s)
    tag.lineTo(0.95 * s, 0.83 * s)
    tag.lineTo(0.38 * s, 0.83 * s)
    tag.closeSubpath()
    hole = QPainterPath()
    hole.addEllipse(QPointF(0.36 * s, 0.5 * s), 0.08 * s, 0.08 * s)
    return tag.subtracted(hole)
