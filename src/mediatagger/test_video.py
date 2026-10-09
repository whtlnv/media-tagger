import subprocess

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


@pytest.fixture
def playing_video(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4", duration=30)
    engine = new_engine(vo="null", ao="null")
    try:
        player = VideoPlayer(engine)
        player.show(clip)
        wait_until_playing(engine)
        yield player, engine
    finally:
        engine.terminate()


def test_showing_a_video_starts_it_playing_unpaused_and_unmuted(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4")
    engine = new_engine(vo="null", ao="null", pause=True, mute=True)
    try:
        VideoPlayer(engine).show(clip)

        wait_until_playing(engine)
        assert engine.path == str(clip)
        assert engine.pause is False
        assert engine.mute is False
    finally:
        engine.terminate()


def test_a_playing_video_restarts_from_the_beginning_when_it_reaches_the_end(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4")
    engine = new_engine(vo="null", ao="null")
    try:
        VideoPlayer(engine).show(clip)

        engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 1.5, timeout=5)
        engine.wait_for_property("time-pos", lambda pos: pos is None or pos < 1.0, timeout=5)
        assert engine.path == str(clip)
        assert engine.time_pos < 1.0
    finally:
        engine.terminate()


def test_pressing_p_on_a_playing_video_pauses_it(playing_video):
    player, engine = playing_video

    player.press("p")

    assert engine.pause is True


def test_pressing_p_on_a_paused_video_resumes_it(playing_video):
    player, engine = playing_video
    player.press("p")

    player.press("p")

    assert engine.pause is False


def test_pressing_enter_toggles_a_video_between_playing_and_paused(playing_video):
    player, engine = playing_video

    player.press("Enter")
    paused_after_first_press = engine.pause
    player.press("Enter")

    assert paused_after_first_press is True
    assert engine.pause is False


def test_pressing_space_on_a_playing_video_does_not_pause_it(playing_video):
    player, engine = playing_video

    player.press("Space")

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


def test_pressing_m_on_a_video_mutes_it(playing_video):
    player, engine = playing_video

    player.press("m")

    assert engine.mute is True


def test_pressing_m_on_a_muted_video_unmutes_it(playing_video):
    player, engine = playing_video
    player.press("m")

    player.press("m")

    assert engine.mute is False


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
