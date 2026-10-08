class VideoPlayer:
    def __init__(self, engine):
        self.engine = engine

    def show(self, path):
        self.engine.play(str(path))
        self.engine.pause = False
        self.engine.mute = False
