from PySide6.QtCore import QEvent, QObject, Qt

from mediatagger.chapter_list import ChapterList
from mediatagger.folder import is_video

_LANDED = 0.5  # a jump lands this close to its moment, give or take a frame: the next jump goes past it
_REPLAYING = 1.0  # `,` within this long after a moment goes to the one before it


def _next(moments, now):
    return next((moment for moment in moments if moment.seconds > now + _LANDED), None)


def _previous(moments, now):
    return next((moment for moment in reversed(moments) if moment.seconds < now - _REPLAYING), None)

_JUMPS = {Qt.Key.Key_Period: _next, Qt.Key.Key_Comma: _previous}


class Chapters(QObject):
    """A video's chapters in the viewer: `c` opens the tag prompt to add one. It watches the viewer's keys ahead of the
    viewer itself, and leaves every key it doesn't use to it."""

    def __init__(self, viewer):
        super().__init__(viewer)
        self._viewer = viewer
        self._read = (None, [])  # the item whose moments were read last, and its moments
        self.list = ChapterList(viewer)
        viewer.installEventFilter(self)
        viewer.progress_bar.moments = lambda: [moment.seconds for moment in self._moments()]

    def read(self, library, path):
        """Reads the item's moments afresh: it was just shown, or its tags changed."""
        self._read = (path, library.moments(path))
        self._viewer.progress_bar.wake()  # its ticks change at once

    def eventFilter(self, watched, event):
        if event.type() != QEvent.Type.KeyPress or event.modifiers() or not self._video_shown():
            return False
        if event.key() == Qt.Key.Key_C:
            self._open_prompt()
            return True
        if event.key() == Qt.Key.Key_L:
            if self.list.isVisible():
                self.list.hide()
            else:
                self.list.show_moments(self._moments())
            return True
        if event.key() in _JUMPS:
            self._jump(_JUMPS[event.key()])
            return True
        return False

    def _jump(self, choose):
        """Seeks to the moment choose picks from the moments and the playback time; with none, stays put."""
        player = self._viewer.video_player
        now = player.engine.time_pos
        moment = None if now is None else choose(self._moments(), now)
        if moment is None:
            return
        player.seek_to(moment.seconds)
        self._viewer.progress_bar.wake(label=", ".join(moment.tags))

    def _open_prompt(self):
        viewer = self._viewer
        if not viewer.session.tags_can_be_saved():
            viewer.status_bar.flash_cant_save()
            return
        library, at = viewer.session.library, viewer.video_player.engine.time_pos
        viewer.tag_prompt.open(library, viewer.slideshow.current, enter=lambda video, text: library.add_chapter(video, text, at))

    def _moments(self):
        """The shown video's moments, as last read; none for anything else."""
        path, moments = self._read
        slideshow = self._viewer.slideshow
        return moments if slideshow is not None and slideshow.current == path else []

    def _video_shown(self):
        slideshow = self._viewer.slideshow
        return slideshow is not None and is_video(slideshow.current)
