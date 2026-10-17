from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QImageIOHandler, QImageReader


def fitted_rect(size, bounds):
    target = QRect(QPoint(), size.scaled(bounds.size(), Qt.AspectRatioMode.KeepAspectRatio))
    target.moveCenter(bounds.center())
    return target


def turned(size, turn):
    """size as it lies turned turn degrees clockwise (a multiple of 90): a quarter turn swaps its sides."""
    return size.transposed() if turn % 180 else size


def draw_turned(painter, image, target, turn):
    """Draw image turned turn degrees clockwise (a multiple of 90) so that it fills target, without copying it turned."""
    painter.translate(target.center())
    painter.rotate(turn)
    upright = QRectF(QPointF(), turned(target.size(), turn))
    upright.moveCenter(QPointF())
    painter.drawImage(upright, image)


def decode_fitted(path, bounds):
    """Decode an image no larger than bounds, so a 12 MP photo is never fully decoded just to be shrunk."""
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    size = reader.size()
    if reader.transformation() & QImageIOHandler.Transformation.TransformationRotate90:
        bounds = bounds.transposed()
    if size.isValid() and (size.width() > bounds.width() or size.height() > bounds.height()):
        reader.setScaledSize(size.scaled(bounds, Qt.AspectRatioMode.KeepAspectRatio))
    return reader.read()
