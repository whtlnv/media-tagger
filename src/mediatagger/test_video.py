import subprocess
import threading
from contextlib import contextmanager

import pytest

from mediatagger.video import VideoPlayer, new_engine


def make_clip(path, duration=2):
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc=duration={duration}:size=64x48:rate=10",
         "-f", "lavfi", "-i", f"sine=duration={duration}", "-shortest", str(path)],
        check=True,
    )
    return path


def wait_until_playing(engine):
    engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 0, timeout=5)


@contextmanager
def silent_engine(**options):
    engine = new_engine(vo="null", ao="null", **options)
    try:
        yield engine
    finally:
        engine.terminate()


@pytest.fixture
def playing_video(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4", duration=30)
    with silent_engine() as engine:
        player = VideoPlayer(engine)
        player.show(clip)
        wait_until_playing(engine)
        yield player, engine


def test_showing_a_video_starts_it_playing_unpaused_and_unmuted(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4")
    with silent_engine(pause=True, mute=True) as engine:
        VideoPlayer(engine).show(clip)

        wait_until_playing(engine)
        assert engine.path == str(clip)
        assert engine.pause is False
        assert engine.mute is False


def test_a_playing_video_restarts_from_the_beginning_when_it_reaches_the_end(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4")
    with silent_engine() as engine:
        VideoPlayer(engine).show(clip)

        engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 1.5, timeout=5)
        engine.wait_for_property("time-pos", lambda pos: pos is None or pos < 1.0, timeout=5)
        assert engine.path == str(clip)
        assert engine.time_pos < 1.0


@pytest.mark.parametrize("keys, setting, value", [
    pytest.param(["p"], "pause", True, id="p on a playing video pauses it"),
    pytest.param(["p", "p"], "pause", False, id="p on a paused video resumes it"),
    pytest.param(["Space"], "pause", False, id="space on a playing video does not pause it"),
    pytest.param(["m"], "mute", True, id="m on a video mutes it"),
    pytest.param(["m", "m"], "mute", False, id="m on a muted video unmutes it"),
])
def test_pressing_a_playback_key_on_a_playing_video_sets_its_pause_or_mute(playing_video, keys, setting, value):
    player, engine = playing_video

    for key in keys:
        player.press(key)

    assert getattr(engine, setting) is value


def test_pressing_enter_toggles_a_video_between_playing_and_paused(playing_video):
    player, engine = playing_video

    player.press("Enter")
    paused_after_first_press = engine.pause
    player.press("Enter")

    assert paused_after_first_press is True
    assert engine.pause is False


def test_moving_from_a_video_with_space_stops_its_playback_and_sound(playing_video):
    player, engine = playing_video

    player.press("Space")

    assert engine.path is None


def test_pressing_up_on_a_video_seeks_10_seconds_forward(playing_video):
    player, engine = playing_video
    before = engine.time_pos

    player.press("Up")

    assert engine.time_pos == pytest.approx(before + 10, abs=1)


def test_pressing_down_on_a_video_seeks_10_seconds_back(playing_video):
    player, engine = playing_video
    with engine.prepare_and_wait_for_event("playback_restart"):
        engine.seek(20, reference="absolute", precision="exact")
    before = engine.time_pos

    player.press("Down")

    assert engine.time_pos == pytest.approx(before - 10, abs=1)


def test_pressing_i_f_right_or_left_on_a_playing_video_does_not_pause_it(playing_video):
    player, engine = playing_video

    paused_after_each_press = []
    for key in ["i", "f", "Right", "Left"]:
        player.press(key)
        paused_after_each_press.append(engine.pause)

    assert paused_after_each_press == [False, False, False, False]


def test_moving_from_a_video_with_right_or_left_stops_its_playback_and_sound(playing_video):
    player, engine = playing_video
    clip = engine.path

    path_after_each_press = []
    for key in ["Right", "Left"]:
        player.show(clip)
        wait_until_playing(engine)
        player.press(key)
        path_after_each_press.append(engine.path)

    assert path_after_each_press == [None, None]


def test_showing_a_good_clip_in_place_of_a_playing_one_reports_it_loaded(playing_video, tmp_path):
    player, engine = playing_video
    other = make_clip(tmp_path / "other.mp4")

    assert player.show(other) is True
    assert engine.path == str(other)


def test_a_clip_that_does_not_load_within_the_time_limit_is_reported_unplayable_instead_of_blocking(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4")
    with silent_engine() as engine:
        assert VideoPlayer(engine, timeout=0.000001).show(clip) is False


@pytest.mark.parametrize("key, ignored_command", [("Up", "seek"), ("Down", "seek"), ("Space", "stop")])
def test_a_seek_or_stop_that_mpv_never_finishes_gives_up_instead_of_blocking(playing_video, monkeypatch, key, ignored_command):
    player, engine = playing_video
    player.timeout = 0.5
    monkeypatch.setattr(engine, ignored_command, lambda *args, **kwargs: None)  # mpv never confirms it

    pressing = threading.Thread(target=player.press, args=(key,), daemon=True)
    pressing.start()
    pressing.join(timeout=3)

    assert not pressing.is_alive()
