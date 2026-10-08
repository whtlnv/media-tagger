class VideoPlayer:
    def __init__(self, engine):
        self.engine = engine

    def show(self, path):
        self.engine.loop_file = "inf"
        self.engine.play(str(path))
        self.engine.pause = False
        self.engine.mute = False

    def press(self, key):
        if key == "Space":
            self.engine.stop()
            self.engine.wait_for_property("path", lambda path: path is None)
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
        with self.engine.prepare_and_wait_for_event("playback_restart"):
            self.engine.seek(seconds, precision="exact")
