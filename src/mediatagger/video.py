import locale

import mpv


def new_engine(**options):
    """libmpv refuses to start unless LC_NUMERIC is "C", and QApplication resets it from the environment."""
    locale.setlocale(locale.LC_NUMERIC, "C")
    return mpv.MPV(**options)


WAIT_SECONDS = 5  # longest the UI waits on mpv; a file that takes longer counts as unplayable


class VideoPlayer:
    def __init__(self, engine, timeout=WAIT_SECONDS):
        self.engine = engine
        self.timeout = timeout

    def show(self, path):
        """Load and play path; True once it has loaded, False if mpv ended it or it didn't load within the timeout."""
        self.engine.loop_file = "inf"
        try:
            with self.engine.prepare_and_wait_for_event(
                "start_file", "file_loaded", "end_file", cond=_outcome_of_this_load(), timeout=self.timeout
            ) as outcome:
                self.engine.play(str(path))
        except TimeoutError:
            self.engine.stop()
            return False
        self.engine.pause = False
        self.engine.mute = False
        return outcome.result() == mpv.MpvEventID.FILE_LOADED

    def press(self, key):
        if key in ("Space", "Right", "Left"):
            self.engine.stop()
            try:
                self.engine.wait_for_property("path", lambda path: path is None, timeout=self.timeout)
            except TimeoutError:
                pass  # leave it stopping in the background rather than freeze the viewer
            return
        if key == "Up":
            self._seek(10)
            return
        if key == "Down":
            self._seek(-10)
            return
        if key == "m":
            self.engine.mute = not self.engine.mute
            return
        if key in ("p", "Enter"):
            self.engine.pause = not self.engine.pause

    def _seek(self, seconds):
        try:
            with self.engine.prepare_and_wait_for_event("playback_restart", timeout=self.timeout):
                self.engine.seek(seconds, precision="exact")
        except TimeoutError:
            pass  # the seek may still land; the viewer stays responsive either way
        except SystemError:
            pass  # mpv refused the seek; playback carries on where it was


def _outcome_of_this_load():
    """Event filter that ignores the end-file of the clip being replaced: only an end after our start counts."""
    started = False

    def outcome(event):
        nonlocal started
        event_id = event.event_id.value
        if event_id == mpv.MpvEventID.START_FILE:
            started = True
            return False
        if event_id == mpv.MpvEventID.FILE_LOADED or (started and event_id == mpv.MpvEventID.END_FILE):
            return event_id
        return False

    return outcome
