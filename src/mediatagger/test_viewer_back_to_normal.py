from PySide6.QtCore import QPoint, QSize, Qt

from mediatagger.image_fit import decode_fitted
from mediatagger.test_viewer import make_image, shown_viewer_on
from mediatagger.test_viewer_turn import make_corner_marked_landscape
from mediatagger.test_viewer_zoom import scroll, square_viewer_on, viewer_playing_a_clip_in


def test_pressing_0_on_a_photo_zoomed_in_off_its_centre_shows_it_exactly_as_it_was_first_fitted(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red", width=200, height=100)
    viewer = square_viewer_on(qtbot, tmp_path)
    fitted = viewer.grab().toImage()
    scroll(viewer, 3, at=QPoint(60, 100))

    qtbot.keyClick(viewer, Qt.Key.Key_0)

    assert viewer.grab().toImage() == fitted


def test_pressing_0_on_a_photo_turned_once_shows_it_exactly_as_it_was_first_fitted_unturned(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    viewer = square_viewer_on(qtbot, tmp_path)
    fitted = viewer.grab().toImage()
    qtbot.keyClick(viewer, Qt.Key.Key_R)

    qtbot.keyClick(viewer, Qt.Key.Key_0)

    assert viewer.grab().toImage() == fitted


def test_one_press_of_0_on_a_photo_turned_then_zoomed_in_off_its_centre_shows_it_exactly_as_it_was_first_fitted_unturned(qtbot, tmp_path):
    make_corner_marked_landscape(tmp_path / "IMG_1.png")
    viewer = square_viewer_on(qtbot, tmp_path)
    fitted = viewer.grab().toImage()
    qtbot.keyClick(viewer, Qt.Key.Key_R)
    scroll(viewer, 4, at=QPoint(250, 40))

    qtbot.keyClick(viewer, Qt.Key.Key_0)

    assert viewer.grab().toImage() == fitted


def test_pressing_0_on_a_large_photo_turned_then_zoomed_in_in_a_wide_viewer_decodes_it_once_more_fitted_unturned_to_the_window(qtbot, tmp_path, monkeypatch):
    make_image(tmp_path / "IMG_1.png", "red", width=1800, height=900)
    decoded_sizes = []

    def recorded_decode_fitted(path, bounds):
        decoded = decode_fitted(path, bounds)
        decoded_sizes.append(decoded.size())
        return decoded

    monkeypatch.setattr("mediatagger.viewer.decode_fitted", recorded_decode_fitted)
    viewer = shown_viewer_on(qtbot, tmp_path)
    viewer.resize(600, 300)
    qtbot.waitUntil(lambda: viewer.width() == 600)
    qtbot.keyClick(viewer, Qt.Key.Key_R)
    scroll(viewer, 4, at=viewer.rect().center())
    viewer.grab()
    decoded_sizes.clear()

    qtbot.keyClick(viewer, Qt.Key.Key_0)
    viewer.grab()

    assert decoded_sizes == [QSize(600, 300)]  # turned, it would fit 300x600: 300x150


def test_pressing_0_on_a_video_sped_up_to_2x_plays_it_at_1x_again(qtbot, tmp_path):
    viewer, engine = viewer_playing_a_clip_in(qtbot, tmp_path)
    for _ in range(3):
        qtbot.keyClick(viewer, Qt.Key.Key_BracketRight)
    assert engine.speed == 2

    qtbot.keyClick(viewer, Qt.Key.Key_0)

    assert engine.speed == 1


def test_pressing_0_on_a_video_zoomed_in_off_its_centre_shows_it_fitted_and_centred_again(qtbot, tmp_path):
    viewer, engine = viewer_playing_a_clip_in(qtbot, tmp_path)
    scroll(viewer, 3, at=QPoint(20, 20))

    qtbot.keyClick(viewer, Qt.Key.Key_0)

    assert (engine.video_zoom, engine.video_pan_x, engine.video_pan_y) == (0, 0, 0)
