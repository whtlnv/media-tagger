from PySide6.QtCore import Qt

from mediatagger.state import remember_rename, remembered_renames
from mediatagger.status_bar import overlay_label
from mediatagger.tag_prompt import TAG_INPUT_STYLE, TagInput, give_tag_suggestions_to, place_above_the_status_bar, prompt_width


class _RecallingInput(TagInput):
    """The rename input: ↑ and ↓ step through the entries remembered in the state file, like the search bar's."""

    def __init__(self, state_file, parent):
        super().__init__(parent)
        self.state_file = state_file
        self.recalled = 0

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            renames = remembered_renames(self.state_file)
            if renames:
                self.recalled = min(self.recalled + 1, len(renames))
                self.setText(renames[-self.recalled])
            return
        if event.key() == Qt.Key.Key_Down:
            if self.recalled:
                self.recalled -= 1
                self.setText(remembered_renames(self.state_file)[-self.recalled] if self.recalled else "")
            return
        super().keyPressEvent(event)


class RenamePrompt:
    """The `n` prompt over a grid, in the tag prompt's style and place: `Rename tag:` shown above an input taking the old
    tag and the new one. Enter hands the entry to on_enter."""

    def __init__(self, host, status_bar, state_file, on_enter):
        self._host = host
        self._status_bar = status_bar
        self.input = _RecallingInput(state_file, host)
        self.input.setStyleSheet(TAG_INPUT_STYLE)
        give_tag_suggestions_to(self.input)
        self.input.returnPressed.connect(self._enter)
        self._on_enter = on_enter
        self.input.hide()
        self.label = overlay_label("Rename tag:", host)
        self.label.hide()

    def _enter(self):
        self._on_enter(self.input.text())

    def is_open(self):
        return self.input.isVisible()

    def open(self, tags):
        self.input.clear()
        self.input.recalled = 0
        self.input.completer().model().setStringList(tags)
        self.input.resize(prompt_width(self._host), self.input.sizeHint().height())
        self.label.adjustSize()
        self.place()
        self.input.show()
        self.label.show()
        self.input.raise_()
        self.label.raise_()
        self.input.setFocus()

    def place(self):
        place_above_the_status_bar(self._host, self._status_bar, self.input, self.label)

    def close_applied(self):
        """Closes the prompt once its entry has been applied, remembering the entry for ↑."""
        remember_rename(self.input.state_file, self.input.text())
        self.close()

    def close(self):
        self.input.hide()
        self.label.hide()
        self._status_bar.show_couldnt_save(False)  # it was about this prompt's entry
        self._host.setFocus()  # keys go back to the host, not to the hidden input
