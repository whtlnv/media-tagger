from PySide6.QtCore import QObject, Signal

from mediatagger.thumbnail_cache import generate_through_cache
from mediatagger.thumbnail_scheduler import ThumbnailScheduler
from mediatagger.thumbnails import thumbnail_and_duration


class FolderThumbnails(QObject):
    """One folder's thumbnails, for its grid. Requested files (the tiles in view) come back through `arrived`, from the
    cache or freshly generated. The rest of the folder is only generated into the cache, never decoded for display, so
    a folder of thousands holds no more pictures than its grid shows. `progress` counts what had to be generated."""

    arrived = Signal(object, object, object)  # path, thumbnail or None, duration or None
    progress = Signal(int, int)  # generated, to generate

    def __init__(self, paths, cache, parent, generate=thumbnail_and_duration):
        super().__init__(parent)
        self._paths = paths
        self._cache = cache
        self._scheduler = ThumbnailScheduler(
            lambda path: generate_through_cache(cache, generate, path),
            prefetch=lambda path: generate_through_cache(cache, generate, path)[2],
            parent=self,
        )
        self._scheduler.generated.connect(self._receive)
        self._scheduler.prefetched.connect(self._count)
        self._scheduler.surveyed.connect(self._prefetch)
        self._generated = set()
        self._to_generate = None  # unknown until the survey of the cache comes back

    def start(self):
        cache, paths = self._cache, self._paths
        self._scheduler.survey(lambda: cache.still_to_generate(paths))

    def request(self, path):
        self._scheduler.request(path)

    def stop(self):
        self._scheduler.shut_down()

    def _receive(self, path, generated):
        thumbnail, duration, was_generated = generated
        self.arrived.emit(path, thumbnail, duration)
        self._count(path, was_generated)

    def _count(self, path, was_generated):
        if was_generated:
            self._generated.add(path)
            self._report()

    def _prefetch(self, still_to_generate):
        self._to_generate = set(still_to_generate)
        self._scheduler.enter_folder([path for path in still_to_generate if path not in self._generated])
        self._report()

    def _report(self):
        if self._to_generate is None:
            return
        total = len(self._to_generate | self._generated)
        if total:
            self.progress.emit(len(self._generated), total)
