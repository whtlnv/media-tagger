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


def shown_height(viewer, column):
    """How many rows of the viewer's centre column show the (red) picture."""
    frame = viewer.grab().toImage()
    return sum(1 for y in range(frame.height()) if frame.pixelColor(column, y).red() > 128)


def test_scrolling_the_mouse_wheel_down_one_notch_over_a_zoomed_in_image_shows_it_smaller_but_no_smaller_than_fitted(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red", width=200, height=100)
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.resize(300, 300)
    qtbot.waitUntil(lambda: viewer.size().width() == viewer.size().height())
    centre = viewer.rect().center()
    fitted = shown_height(viewer, centre.x())
    scroll(viewer, 2, at=centre)
    zoomed_in = shown_height(viewer, centre.x())

    scroll(viewer, -1, at=centre)

    assert fitted < shown_height(viewer, centre.x()) < zoomed_in


def test_scrolling_the_mouse_wheel_up_many_notches_over_an_image_stops_at_three_times_its_fitted_size(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red", width=200, height=20)
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.resize(300, 300)
    qtbot.waitUntil(lambda: viewer.size().width() == viewer.size().height())
    centre = viewer.rect().center()

    def picture_rows():  # rows of the centre column above the overlays (from y 250 down) showing the picture
        frame = viewer.grab().toImage()
        return sum(1 for y in range(250) if frame.pixelColor(centre.x(), y).red() > 128)

    fitted = picture_rows()  # fitted 300x30 at y 135..164, so 3x is 90 rows at y 105..194

    scroll(viewer, 20, at=centre)

    assert picture_rows() == 3 * fitted
