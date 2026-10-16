from PySide6.QtCore import QEvent, QObject, Qt

from mediatagger.folder import is_video


class Chapters(QObject):
    """A video's chapters in the viewer: `c` opens the tag prompt to add one. It watches the viewer's keys ahead of the
    viewer itself, and leaves every key it doesn't use to it."""

    def __init__(self, viewer):
        super().__init__(viewer)
        self._viewer = viewer
        self._read = (None, [])  # the item whose moments were read last, and its moments
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
        return False

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
