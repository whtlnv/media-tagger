import sqlite3

from PySide6.QtCore import QEvent, QObject, Qt

from mediatagger.chapter_list import ChapterList
from mediatagger.folder import is_video

_LANDED = 0.5  # a jump lands this close to its moment, give or take a frame: the next jump goes past it
_REPLAYING = 1.0  # `,` within this long after a moment goes to the one before it


def _next(moments, now, backwards=False):
    """Playing backwards, a moment passed within the last second is the one just landed on: the next goes past it."""
    landed = _REPLAYING if backwards else _LANDED
    return next((moment for moment in moments if moment.seconds > now + landed), None)


def _previous(moments, now, backwards=False):
    return next((moment for moment in reversed(moments) if moment.seconds < now - _REPLAYING), None)


_JUMPS = {Qt.Key.Key_Period: _next, Qt.Key.Key_Comma: _previous}
_MOVES = {Qt.Key.Key_Space, Qt.Key.Key_Left, Qt.Key.Key_Right}  # the viewer's keys to another item
_LIST_STEPS = {Qt.Key.Key_Down: 1, Qt.Key.Key_Up: -1}
_LIST_KEYS = {*_LIST_STEPS, Qt.Key.Key_Return, Qt.Key.Key_Escape, Qt.Key.Key_Backspace}


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
        if self._viewer.tag_prompt.has_focus():
            return False  # a key the tag prompt passes on
        if event.key() == Qt.Key.Key_C:
            self._open_prompt()
            return True
        if event.key() in _MOVES:
            self.list.hide()  # it lists the item being left
            return False
        if self.list.isVisible() and event.key() in _LIST_KEYS:
            self._in_list(event.key())
            return True
        if event.key() == Qt.Key.Key_L:
            if self.list.isVisible():
                self.list.hide()
            else:
                self.list.show_moments(self._moments())
            return True
        if event.key() in _JUMPS:
            jump, backwards = _JUMPS[event.key()], self._viewer.video_player.backwards
            self._jump(lambda moments, now: jump(moments, now, backwards))
            return True
        return False

    def _in_list(self, key):
        """While the chapter list is shown: ↑/↓ move its highlight, Enter jumps to that moment, Esc closes it."""
        if key in _LIST_STEPS:
            self.list.step(_LIST_STEPS[key])
            return
        if key == Qt.Key.Key_Backspace:
            self._delete_highlighted()
            return
        self.list.hide()
        row = self.list.currentRow()
        if key == Qt.Key.Key_Return and row >= 0:
            self._jump(lambda moments, now: moments[row])

    def _delete_highlighted(self):
        """Backspace in the chapter list: the highlighted moment goes, where tags can be saved; its tags stay."""
        viewer, row = self._viewer, self.list.currentRow()
        if row < 0:
            return
        if not viewer.session.tags_can_be_saved():
            viewer.status_bar.flash_cant_save()
            return
        library, video = viewer.session.library, viewer.slideshow.current
        try:
            library.delete_moment(video, self._moments()[row].seconds)
        except (sqlite3.Error, OSError):
            viewer.status_bar.flash_cant_save()
            return
        self.read(library, video)
        self.list.show_moments(self._moments(), row=row)

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
        library, at = viewer.session.library, viewer.video_player.engine.time_pos or 0  # none while it can't play
        viewer.tag_prompt.open(library, viewer.slideshow.current, enter=lambda video, text: library.add_chapter(video, text, at))

    def _moments(self):
        """The shown video's moments, as last read; none for anything else."""
        path, moments = self._read
        slideshow = self._viewer.slideshow
        return moments if slideshow is not None and slideshow.current == path else []

    def _video_shown(self):
        slideshow = self._viewer.slideshow
        return slideshow is not None and is_video(slideshow.current)
