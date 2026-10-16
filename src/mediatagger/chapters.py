from PySide6.QtCore import QEvent, QObject, Qt

from mediatagger.folder import is_video


class Chapters(QObject):
    """A video's chapters in the viewer: `c` opens the tag prompt to add one. It watches the viewer's keys ahead of the
    viewer itself, and leaves every key it doesn't use to it."""

    def __init__(self, viewer):
        super().__init__(viewer)
        self._viewer = viewer
        viewer.installEventFilter(self)

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

    def _video_shown(self):
        slideshow = self._viewer.slideshow
        return slideshow is not None and is_video(slideshow.current)
