import subprocess

import mpv

from mediatagger.video import VideoPlayer


def make_clip(path):
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=duration=2:size=64x48:rate=10",
         "-f", "lavfi", "-i", "sine=duration=2", "-shortest", str(path)],
        check=True,
    )
    return path


def test_showing_a_video_starts_it_playing_unpaused_and_unmuted(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4")
    engine = mpv.MPV(vo="null", ao="null", pause=True, mute=True)
    try:
        VideoPlayer(engine).show(clip)

        engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 0, timeout=5)
        assert engine.path == str(clip)
        assert engine.pause is False
        assert engine.mute is False
    finally:
        engine.terminate()


def test_a_playing_video_restarts_from_the_beginning_when_it_reaches_the_end(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4")
    engine = mpv.MPV(vo="null", ao="null")
    try:
        VideoPlayer(engine).show(clip)

        engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 1.5, timeout=5)
        engine.wait_for_property("time-pos", lambda pos: pos is None or pos < 1.0, timeout=5)
        assert engine.path == str(clip)
        assert engine.time_pos < 1.0
    finally:
        engine.terminate()


def test_pressing_p_on_a_playing_video_pauses_it(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4")
    engine = mpv.MPV(vo="null", ao="null")
    try:
        player = VideoPlayer(engine)
        player.show(clip)
        engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 0, timeout=5)

        player.press("p")

        assert engine.pause is True
    finally:
        engine.terminate()


def test_pressing_p_on_a_paused_video_resumes_it(tmp_path):
    clip = make_clip(tmp_path / "clip.mp4")
    engine = mpv.MPV(vo="null", ao="null")
    try:
        player = VideoPlayer(engine)
        player.show(clip)
        engine.wait_for_property("time-pos", lambda pos: pos is not None and pos > 0, timeout=5)
        player.press("p")

        player.press("p")

        assert engine.pause is False
    finally:
        engine.terminate()
