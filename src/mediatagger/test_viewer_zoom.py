from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QWheelEvent
from PySide6.QtWidgets import QApplication

from mediatagger.test_viewer import make_image, shown_viewer_on

NOTCH = 120


def scroll(viewer, notches, at):
    """Turns the mouse wheel over the viewer at a point: positive notches scroll up."""
    event = QWheelEvent(
        QPointF(at), QPointF(viewer.mapToGlobal(at)), QPoint(0, 0), QPoint(0, notches * NOTCH),
        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False,
    )
    QApplication.sendEvent(viewer, event)


def test_scrolling_the_mouse_wheel_up_one_notch_over_a_fitted_image_shows_it_larger_than_fitted(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red", width=200, height=100)
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.resize(300, 300)
    qtbot.waitUntil(lambda: viewer.size().width() == viewer.size().height())
    just_above_the_fitted_image = QPoint(150, 70)  # fitted 300x150 at y 75..224
    assert viewer.grab().toImage().pixelColor(just_above_the_fitted_image) == QColor("black")

    scroll(viewer, 1, at=viewer.rect().center())

    assert viewer.grab().toImage().pixelColor(just_above_the_fitted_image) == QColor("red")


def test_scrolling_the_mouse_wheel_down_one_notch_over_a_fitted_image_leaves_it_fitted(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red", width=200, height=100)
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.resize(300, 300)
    qtbot.waitUntil(lambda: viewer.size().width() == viewer.size().height())
    fitted = viewer.grab().toImage()

    scroll(viewer, -1, at=viewer.rect().center())

    assert viewer.grab().toImage() == fitted
