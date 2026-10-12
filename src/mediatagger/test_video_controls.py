from types import SimpleNamespace

import shiboken6
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from mediatagger.test_video import make_clip
from mediatagger.test_viewer import (
    make_folder_with_no_media,
    make_image,
    shown_texts,
    shown_viewer_on,
    shows_video_surface,
    wait_until_loaded,
)
from mediatagger.test_viewer_open import drag_and_drop_onto
from mediatagger.video_controls import ProgressBar
from mediatagger.viewer import UNSUPPORTED_TEXT


def test_a_starting_video_shows_a_progress_bar_at_zero_of_its_length_that_hides_once_a_folder_with_no_media_is_dropped(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    empty = make_folder_with_no_media(tmp_path / "Holidays")
    viewer = shown_viewer_on(qtbot, tmp_path)
    wait_until_loaded(viewer.video_player.engine, clip)

    bar = viewer.findChild(ProgressBar)
    assert bar is not None and bar.isVisible()
    qtbot.waitUntil(lambda: bar.text() == "0:00 / 1:05", timeout=5000)

    drag_and_drop_onto(viewer, empty)

    assert not bar.isVisible()


def test_moving_from_a_playing_video_to_one_that_cannot_be_played_shows_the_unsupported_placeholder_and_no_progress_bar(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    (tmp_path / "IMG_2.mp4").write_bytes(b"not really an mp4")
    viewer = shown_viewer_on(qtbot, tmp_path)
    wait_until_loaded(viewer.video_player.engine, clip)
    bar = viewer.findChild(ProgressBar)
    qtbot.waitUntil(bar.isVisible, timeout=5000)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    qtbot.waitUntil(lambda: UNSUPPORTED_TEXT in shown_texts(viewer), timeout=5000)
    assert not bar.isVisible()


def test_moving_from_a_playing_video_to_an_image_shows_the_image_and_no_progress_bar(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_viewer_on(qtbot, tmp_path)
    wait_until_loaded(viewer.video_player.engine, clip)
    bar = viewer.findChild(ProgressBar)
    qtbot.waitUntil(bar.isVisible, timeout=5000)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    qtbot.waitUntil(lambda: not shows_video_surface(viewer), timeout=5000)
    assert not bar.isVisible()


def test_while_a_video_plays_the_progress_bar_elapsed_time_advances(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    viewer = shown_viewer_on(qtbot, tmp_path)
    wait_until_loaded(viewer.video_player.engine, clip)
    bar = viewer.findChild(ProgressBar)

    qtbot.waitUntil(lambda: bar.text() == "0:01 / 1:05", timeout=5000)


def test_while_mpv_reports_no_position_or_length_between_clips_the_progress_bar_keeps_its_text_and_raises_nothing(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    bar = ProgressBar(parent)
    parent.show()
    qtbot.waitExposed(parent)
    engine = SimpleNamespace(duration=65, time_pos=0)
    bar.start(engine)

    engine.duration = engine.time_pos = None  # what a stopped mpv reports
    qtbot.wait(600)

    assert bar.text() == "0:00 / 1:05"


def test_half_way_through_a_video_the_progress_bar_is_filled_up_to_its_middle(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    bar = ProgressBar(parent)
    bar.resize(200, 20)
    bar.start(SimpleNamespace(duration=60, time_pos=30))
    parent.show()
    qtbot.waitUntil(lambda: bar.text().startswith("0:30"))

    image = bar.grab().toImage()
    row = 1  # above the text
    filled, empty = image.pixelColor(10, row), image.pixelColor(190, row)

    assert filled != empty
    assert image.pixelColor(90, row) == filled
    assert image.pixelColor(110, row) == empty


def test_a_video_shorter_than_an_hour_shows_its_times_as_minutes_and_seconds(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    bar = ProgressBar(parent)
    parent.show()
    qtbot.waitExposed(parent)

    bar.start(SimpleNamespace(duration=4 * 60 + 56, time_pos=60 + 23))

    qtbot.waitUntil(lambda: bar.text() == "1:23 / 4:56")


def test_a_video_of_an_hour_or_more_shows_its_times_as_hours_minutes_and_seconds(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    bar = ProgressBar(parent)
    parent.show()
    qtbot.waitExposed(parent)

    bar.start(SimpleNamespace(duration=60 * 60 + 2 * 60 + 3, time_pos=5))

    qtbot.waitUntil(lambda: bar.text() == "0:00:05 / 1:02:03")


def test_destroying_a_shown_progress_bar_whose_attributes_the_garbage_collector_already_cleared_raises_nothing(qtbot):
    parent = QWidget()
    bar = ProgressBar(parent)
    parent.show()
    qtbot.waitExposed(parent)
    bar.show()

    bar.__dict__.clear()  # what Python's GC does to the wrapper when it breaks a reference cycle
    shiboken6.delete(parent)  # Qt hides the still-shown bar while destroying it


def test_with_no_input_for_the_hide_delay_the_progress_bar_hides(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    bar = ProgressBar(parent, hide_delay=100)
    parent.show()
    qtbot.waitExposed(parent)

    bar.start(SimpleNamespace(duration=65, time_pos=0))

    assert bar.isVisible()
    qtbot.waitUntil(lambda: not bar.isVisible(), timeout=2000)


def test_a_key_pressed_while_the_progress_bar_is_hidden_on_a_playing_video_shows_it_again(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    viewer = shown_viewer_on(qtbot, tmp_path)
    wait_until_loaded(viewer.video_player.engine, clip)
    bar = viewer.findChild(ProgressBar)
    qtbot.waitUntil(bar.isVisible, timeout=5000)
    bar.hide()  # as when the hide delay runs out

    qtbot.keyClick(viewer, Qt.Key.Key_A)

    assert bar.isVisible()
