import re
import time
from types import SimpleNamespace

import mpv
import pytest
import shiboken6
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLineEdit, QStackedWidget, QWidget

from mediatagger.test_video import make_clip, wait_until_playing
from mediatagger.test_viewer import (
    make_folder_with_no_media,
    SILENT,
    make_image,
    make_surface_ready,
    show_exposed,
    shown_texts,
    shown_viewer_on,
    shows_video_surface,
    wait_until_loaded,
)
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_clip
from mediatagger.test_viewer_open import drag_and_drop_onto
from mediatagger.test_viewer_video import FRAME_STEPPING, pause_at_10_seconds, viewer_paused_at_10_seconds
from mediatagger.video_controls import HIDE_DELAY_MS, ProgressBar
from mediatagger.viewer import UNSUPPORTED_TEXT
from mediatagger.window import Window


def fake_engine(duration, time_pos, speed=1):
    """What the bar reads of an mpv player: its length, position and playback speed."""
    return SimpleNamespace(duration=duration, time_pos=time_pos, speed=speed)


def viewer_playing_with_its_progress_bar(qtbot, folder, clip):
    viewer = shown_viewer_on(qtbot, folder)
    wait_until_loaded(viewer.video_player.engine, clip)
    bar = viewer.findChild(ProgressBar)
    qtbot.waitUntil(bar.isVisible, timeout=5000)
    return viewer, bar


def shown_progress_bar(qtbot, hide_delay=HIDE_DELAY_MS):
    """A bar in a shown parent of its own. The parent comes back too: once nothing holds it, Qt deletes it with the bar."""
    parent = QWidget()
    qtbot.addWidget(parent)
    bar = ProgressBar(parent, hide_delay=hide_delay)
    parent.show()
    qtbot.waitExposed(parent)
    return parent, bar


def progress_bar_over(qtbot, background, size, engine):
    """A bar of this size, started on this engine, in a shown frame of this background colour, which comes back too."""
    frame = QWidget()
    frame.setStyleSheet(f"background: {background}")
    qtbot.addWidget(frame)
    bar = ProgressBar(frame)
    bar.resize(*size)
    bar.start(engine)
    frame.show()
    qtbot.waitExposed(frame)
    return frame, bar


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
    viewer, bar = viewer_playing_with_its_progress_bar(qtbot, tmp_path, clip)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    qtbot.waitUntil(lambda: UNSUPPORTED_TEXT in shown_texts(viewer), timeout=5000)
    assert not bar.isVisible()


def test_moving_from_a_playing_video_to_an_image_shows_the_image_and_no_progress_bar(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    make_image(tmp_path / "IMG_2.png", "red")
    viewer, bar = viewer_playing_with_its_progress_bar(qtbot, tmp_path, clip)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    qtbot.waitUntil(lambda: not shows_video_surface(viewer), timeout=5000)
    assert not bar.isVisible()


def test_while_a_video_plays_the_progress_bar_elapsed_time_advances(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    viewer, bar = viewer_playing_with_its_progress_bar(qtbot, tmp_path, clip)

    qtbot.waitUntil(lambda: bar.text() == "0:01 / 1:05", timeout=5000)


def test_while_mpv_reports_no_position_or_length_between_clips_the_progress_bar_keeps_its_text_and_raises_nothing(qtbot):
    parent, bar = shown_progress_bar(qtbot)
    engine = fake_engine(duration=65, time_pos=0)
    bar.start(engine)

    engine.duration = engine.time_pos = None  # what a stopped mpv reports
    qtbot.wait(600)

    assert bar.text() == "0:00 / 1:05"


def test_half_way_through_a_video_the_progress_bar_is_filled_up_to_its_middle(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    bar = ProgressBar(parent)
    bar.resize(200, 20)
    bar.start(fake_engine(duration=60, time_pos=30))
    parent.show()
    qtbot.waitUntil(lambda: bar.text().startswith("0:30"))

    image = bar.grab().toImage()
    row = image.height() - 2  # the track along the bottom edge
    filled, empty = image.pixelColor(10, row), image.pixelColor(190, row)

    assert filled != empty
    assert image.pixelColor(90, row) == filled
    assert image.pixelColor(110, row) == empty


@pytest.mark.parametrize("engine, text", [
    pytest.param(fake_engine(duration=4 * 60 + 56, time_pos=60 + 23), "1:23 / 4:56",
                 id="a video shorter than an hour shows its times as minutes and seconds"),
    pytest.param(fake_engine(duration=60 * 60 + 2 * 60 + 3, time_pos=5), "0:00:05 / 1:02:03",
                 id="a video of an hour or more shows its times as hours, minutes and seconds"),
    pytest.param(fake_engine(duration=30, time_pos=0, speed=2), "0:00 / 0:30 · 2×",
                 id="a video playing at 2x shows its times followed by its speed"),
    pytest.param(fake_engine(duration=30, time_pos=0, speed=0.25), "0:00 / 0:30 · 0.25×",
                 id="a video playing at a quarter speed shows its times followed by 0.25x"),
])
def test_the_progress_bar_reads_a_videos_times_and_any_speed_other_than_1x(qtbot, engine, text):
    parent, bar = shown_progress_bar(qtbot)

    bar.start(engine)

    qtbot.waitUntil(lambda: bar.text() == text)


def test_destroying_a_shown_progress_bar_whose_attributes_the_garbage_collector_already_cleared_raises_nothing(qtbot):
    parent = QWidget()
    bar = ProgressBar(parent)
    parent.show()
    qtbot.waitExposed(parent)
    bar.show()

    bar.__dict__.clear()  # what Python's GC does to the wrapper when it breaks a reference cycle
    shiboken6.delete(parent)  # Qt hides the still-shown bar while destroying it


def test_with_no_input_for_the_hide_delay_the_progress_bar_hides(qtbot):
    parent, bar = shown_progress_bar(qtbot, hide_delay=100)

    bar.start(fake_engine(duration=65, time_pos=0))

    assert bar.isVisible()
    qtbot.waitUntil(lambda: not bar.isVisible(), timeout=2000)



def test_destroying_a_shown_progress_bar_that_avoids_a_shown_sibling_after_the_garbage_collector_cleared_its_attributes_raises_nothing(qtbot):
    parent = QWidget()
    bar = ProgressBar(parent)
    sibling = QWidget(parent)
    bar.avoid(sibling)
    parent.show()
    qtbot.waitExposed(parent)

    bar.__dict__.clear()  # what Python's GC does to the wrapper when it breaks a reference cycle
    shiboken6.delete(parent)  # Qt hides the shown sibling while destroying it, which the bar watches

@pytest.mark.parametrize("duration, key, text", [
    pytest.param(65, Qt.Key.Key_A, r"\d:\d\d / 1:05", id="a key with no command shows the bar again"),
    pytest.param(65, Qt.Key.Key_V, r"\d:\d\d / 1:05", id="v shows the bar"),
    pytest.param(65, Qt.Key.Key_Up, r"0:10 / 1:05", id="up shows the bar at the new position"),
    pytest.param(65, Qt.Key.Key_BracketRight, r"\d:\d\d / 1:05 · 1\.25×", id="] shows the bar reading its new speed"),
    pytest.param(90, Qt.Key.Key_5, r"0:40 / 1:30", id="5 seeks to four ninths of its length and shows the bar"),
])
def test_a_key_on_a_playing_video_whose_progress_bar_is_hidden_shows_the_bar_at_once_reading_any_change(qtbot, tmp_path, duration, key, text):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=duration)
    viewer, bar = viewer_playing_with_its_progress_bar(qtbot, tmp_path, clip)
    bar.hide()  # as when the hide delay runs out

    qtbot.keyClick(viewer, key)

    assert bar.isVisible()
    assert re.fullmatch(text, bar.text())


def test_left_bracket_on_a_playing_video_shows_the_bar_reading_its_slower_speed(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    viewer, bar = viewer_playing_with_its_progress_bar(qtbot, tmp_path, clip)

    qtbot.keyClick(viewer, Qt.Key.Key_BracketLeft)

    assert bar.text().endswith(" · 0.75×")


def test_v_on_a_playing_video_leaves_its_pause_mute_position_speed_rotation_and_item_as_they_were(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    make_image(tmp_path / "IMG_2.png", "red")
    viewer, bar = viewer_playing_with_its_progress_bar(qtbot, tmp_path, clip)
    engine = viewer.video_player.engine
    wait_until_playing(engine)
    engine.pause, engine.mute, engine.speed, engine.video_rotate = True, True, 2, 90
    qtbot.wait(300)  # let the pause settle before reading where it stopped
    position = engine.time_pos

    qtbot.keyClick(viewer, Qt.Key.Key_V)
    qtbot.wait(300)

    assert (engine.pause, engine.mute, engine.speed, engine.video_rotate) == (True, True, 2, 90)
    assert engine.time_pos == pytest.approx(position, abs=0.05)
    assert viewer.slideshow.current == clip


def playing_at_30_seconds(viewer):
    engine = viewer.video_player.engine
    wait_until_playing(engine)
    engine.seek(30, reference="absolute", precision="exact")
    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos >= 30, timeout=5)


def test_one_on_a_90_s_video_playing_at_0_30_jumps_back_to_the_start(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=90)
    viewer, bar = viewer_playing_with_its_progress_bar(qtbot, tmp_path, clip)
    playing_at_30_seconds(viewer)

    qtbot.keyClick(viewer, Qt.Key.Key_1)

    assert bar.text() == "0:00 / 1:30"


def test_zero_on_a_90_s_video_playing_at_0_30_leaves_it_playing_on_from_there(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=90)
    viewer, bar = viewer_playing_with_its_progress_bar(qtbot, tmp_path, clip)
    playing_at_30_seconds(viewer)

    qtbot.keyClick(viewer, Qt.Key.Key_0)

    assert re.fullmatch(r"0:3\d / 1:30", bar.text())


def test_waking_the_progress_bar_while_it_shows_keeps_it_visible_for_the_full_hide_delay_after_the_latest_wake(qtbot):
    parent, bar = shown_progress_bar(qtbot, hide_delay=1500)
    bar.start(fake_engine(duration=65, time_pos=0))
    qtbot.wait(1000)

    bar.wake()  # what the viewer does on every key
    qtbot.wait(1000)  # past the first delay, within the second

    assert bar.isVisible()
    qtbot.waitUntil(lambda: not bar.isVisible(), timeout=5000)


def test_the_progress_bar_lies_along_the_bottom_of_a_playing_video_just_above_the_status_bar_not_overlapping_it(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    viewer, bar = viewer_playing_with_its_progress_bar(qtbot, tmp_path, clip)

    frame, status_bar = bar.geometry(), viewer.status_bar.geometry()

    assert frame.bottom() > viewer.height() // 2
    assert not frame.intersects(status_bar)
    assert frame.bottom() < status_bar.top()


def test_in_the_window_the_progress_bar_spans_the_playing_videos_width_just_above_the_windows_status_bar(qtbot, tmp_path):
    clip = make_clip(tmp_path / "a.mp4", duration=65)
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()
    make_surface_ready(viewer)
    wait_until_loaded(viewer.video_player.engine, clip)
    bar = viewer.findChild(ProgressBar)
    qtbot.waitUntil(bar.isVisible, timeout=5000)

    frame = QRect(bar.mapTo(window, QPoint()), bar.size())
    status_top = window.status_bar.geometry().top()

    assert frame.width() == window.width()
    assert frame.bottom() == status_top - 1


def test_in_the_window_right_bracket_then_r_on_an_opened_video_plays_it_at_1_25x_turned_90_degrees(qtbot, tmp_path):
    clip = make_clip(tmp_path / "a.mp4", duration=30)
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    wait_until_loaded(engine, clip)

    qtbot.keyClick(viewer, Qt.Key.Key_BracketRight)
    qtbot.keyClick(viewer, Qt.Key.Key_R)

    assert [engine.speed, engine.video_rotate] == [1.25, 90]


def test_in_the_windows_grid_brackets_r_and_v_leave_the_next_video_opened_starting_at_1x_and_unrotated(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    clip = make_clip(tmp_path / "b.mp4", duration=30)
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    grid = stack.currentWidget()
    for key in (Qt.Key.Key_BracketRight, Qt.Key.Key_BracketLeft, Qt.Key.Key_BracketRight, Qt.Key.Key_R, Qt.Key.Key_V):
        qtbot.keyClick(grid, key)

    qtbot.keyClick(grid, Qt.Key.Key_Right)
    qtbot.keyClick(grid, Qt.Key.Key_Return)
    viewer = stack.currentWidget()
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    wait_until_playing(engine)

    assert engine.path == str(clip)
    assert [engine.speed, engine.video_rotate] == [1, 0]


def test_in_the_window_the_progress_bar_of_a_playing_video_does_not_overlap_the_open_tag_prompt(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=65)
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()
    make_surface_ready(viewer)
    wait_until_loaded(viewer.video_player.engine, folder / "IMG_1.mp4")
    bar = viewer.findChild(ProgressBar)
    qtbot.waitUntil(bar.isVisible, timeout=5000)

    qtbot.keyClick(window, Qt.Key.Key_T)

    [prompt] = [line for line in window.findChildren(QLineEdit) if line.isVisible()]
    bar_frame = QRect(bar.mapTo(window, QPoint()), bar.size())
    prompt_frame = QRect(prompt.mapTo(window, QPoint()), prompt.size())
    assert bar.isVisible()
    assert not bar_frame.intersects(prompt_frame)


def test_the_progress_bar_shows_light_text_and_a_light_filled_track_over_a_black_frame(qtbot):
    engine = fake_engine(duration=60, time_pos=0)
    frame, bar = progress_bar_over(qtbot, "black", (300, 20), engine)

    def lightest(image):
        return max(image.pixelColor(x, y).lightness() for x in range(image.width()) for y in range(image.height()))

    assert lightest(frame.grab(bar.geometry()).toImage()) > 200  # the text reads over a black frame

    engine.time_pos = 30
    qtbot.waitUntil(lambda: bar.text().startswith("0:30"))
    assert frame.grab(bar.geometry()).toImage().pixelColor(5, 18).lightness() > 200  # the filled track reads over a black frame


def test_over_a_white_video_frame_the_progress_bar_outside_its_text_and_track_leaves_the_frame_white(qtbot):
    frame, bar = progress_bar_over(qtbot, "white", (300, 20), fake_engine(duration=60, time_pos=0))

    image = frame.grab(bar.geometry()).toImage()

    assert image.pixelColor(295, 5) == QColor("white")  # right of the text, above the track


def test_over_a_white_video_frame_the_light_elapsed_and_total_text_is_edged_with_dark_pixels(qtbot):
    frame, bar = progress_bar_over(qtbot, "white", (300, 20), fake_engine(duration=60, time_pos=0))

    image = frame.grab(bar.geometry()).toImage()
    text_area = [image.pixelColor(x, y).lightness() for x in range(120) for y in range(20 - 3)]  # left of the bar, above its track

    assert min(text_area) < 64  # the text's dark edge shows against the white frame


def test_over_a_white_video_frame_the_light_filled_part_of_the_track_is_edged_with_dark_pixels(qtbot):
    frame, bar = progress_bar_over(qtbot, "white", (300, 20), fake_engine(duration=60, time_pos=30))
    qtbot.waitUntil(lambda: bar.text().startswith("0:30"))

    image = frame.grab(bar.geometry()).toImage()

    assert image.pixelColor(5, 18).lightness() > 200  # the filled part of the track, along the bottom: light
    assert image.pixelColor(5, 16).lightness() < 64  # just above it: its dark edge against the white frame


def test_over_a_black_video_frame_the_progress_bar_outside_its_text_and_track_leaves_the_frame_black(qtbot):
    frame, bar = progress_bar_over(qtbot, "black", (300, 20), fake_engine(duration=60, time_pos=0))

    image = frame.grab(bar.geometry()).toImage()

    assert image.pixelColor(295, 5) == QColor("black")  # right of the text, above the track


def test_the_filled_track_is_a_thin_strip_along_the_bottom_of_the_progress_bar_so_the_light_text_never_sits_on_it(qtbot):
    parent, bar = progress_bar_over(qtbot, "black", (300, 24), fake_engine(duration=60, time_pos=30))
    qtbot.waitUntil(lambda: bar.text().startswith("0:30"))

    image = parent.grab(bar.geometry()).toImage()

    assert image.pixelColor(5, 2).lightness() < 128  # the filled half's top: still the black frame
    assert image.pixelColor(5, 22).lightness() > 200  # the filled half's bottom edge: the light track


def test_the_progress_bar_of_a_playing_video_is_stacked_above_the_video_surface(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    viewer, bar = viewer_playing_with_its_progress_bar(qtbot, tmp_path, clip)

    on_top = viewer.childAt(bar.geometry().center())

    assert on_top is bar or bar.isAncestorOf(on_top)


def test_closing_the_window_while_a_video_plays_with_its_progress_bar_shown_raises_nothing_on_the_bars_next_tick(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=65)
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()
    make_surface_ready(viewer)
    wait_until_loaded(viewer.video_player.engine, folder / "IMG_1.mp4")
    bar = viewer.findChild(ProgressBar)
    qtbot.waitUntil(bar.isVisible, timeout=5000)
    terminate = mpv.MPV.terminate

    def slow_terminate(engine):  # a slow mpv shutdown: the bar's next tick is due when closing backs up the library
        time.sleep(0.3)
        terminate(engine)

    monkeypatch.setattr(mpv.MPV, "terminate", slow_terminate)

    window.close()  # the backup lets Qt process due timers before the window hides
    qtbot.wait(600)


def is_tick_coloured(colour):
    return colour.red() > 200 and colour.green() > 150 and colour.blue() < 100


def test_a_video_with_a_moment_at_half_its_duration_shows_a_tick_at_the_middle_of_the_progress_bars_track(qtbot):
    engine = fake_engine(duration=60, time_pos=0)
    frame, bar = progress_bar_over(qtbot, "black", (400, 20), engine)

    bar.moments = lambda: [30]
    bar.wake()

    image = frame.grab(bar.geometry()).toImage()
    assert is_tick_coloured(image.pixelColor(200, 18))
    assert not is_tick_coloured(image.pixelColor(190, 18))


def test_a_moment_at_a_quarter_of_the_videos_duration_shows_a_tick_a_quarter_of_the_way_along_the_track(qtbot):
    engine = fake_engine(duration=60, time_pos=0)
    frame, bar = progress_bar_over(qtbot, "black", (400, 20), engine)

    bar.moments = lambda: [15]
    bar.wake()

    image = frame.grab(bar.geometry()).toImage()
    assert is_tick_coloured(image.pixelColor(100, 18))
    assert not is_tick_coloured(image.pixelColor(200, 18))


def test_a_video_with_no_moments_shows_no_tick_on_its_progress_bar(qtbot):
    frame, bar = progress_bar_over(qtbot, "black", (400, 20), fake_engine(duration=60, time_pos=30))
    qtbot.waitUntil(lambda: bar.text().startswith("0:30"))

    image = frame.grab(bar.geometry()).toImage()

    assert not any(is_tick_coloured(image.pixelColor(x, 18)) for x in range(400))


def test_u_on_a_paused_video_whose_progress_bar_is_hidden_shows_the_bar_reading_the_next_frames_time(qtbot, tmp_path):
    viewer = viewer_paused_at_10_seconds(qtbot, tmp_path, rate=1)  # one frame a second, so the step shows in the time
    bar = viewer.findChild(ProgressBar)
    bar.hide()  # as when the hide delay runs out

    qtbot.keyClick(viewer, Qt.Key.Key_U)

    assert bar.isVisible()
    qtbot.waitUntil(lambda: bar.text() == "0:11 / 0:30", timeout=5000)


def test_e_on_a_paused_video_whose_progress_bar_is_hidden_shows_the_bar_reading_the_previous_frames_time(qtbot, tmp_path):
    viewer = viewer_paused_at_10_seconds(qtbot, tmp_path, rate=1)  # one frame a second, so the step shows in the time
    bar = viewer.findChild(ProgressBar)
    bar.hide()  # as when the hide delay runs out

    qtbot.keyClick(viewer, Qt.Key.Key_E)

    assert bar.isVisible()
    qtbot.waitUntil(lambda: bar.text() == "0:09 / 0:30", timeout=5000)


def test_in_the_window_on_a_drive_u_on_a_paused_video_steps_it_one_frame_forward(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=30)  # 10 fps, so one frame is 0.1 s
    window = Window(folder, player_options=FRAME_STEPPING, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()
    make_surface_ready(viewer)
    pause_at_10_seconds(qtbot, viewer)

    qtbot.keyClick(viewer, Qt.Key.Key_U)

    viewer.video_player.engine.wait_for_property("time-pos", lambda time_pos: time_pos == pytest.approx(10.1, abs=0.01), timeout=5)
