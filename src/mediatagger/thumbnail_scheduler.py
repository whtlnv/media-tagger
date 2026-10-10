from concurrent.futures import ThreadPoolExecutor


class ThumbnailScheduler:
    def __init__(self, generate):
        self._generate = generate
        self._executor = ThreadPoolExecutor(max_workers=3)

    def request(self, path):
        self._executor.submit(self._generate, path)
