from PySide6.QtWidgets import QCompleter

from mediatagger.status_bar import overlay_label
from mediatagger.tag_prompt import TAG_INPUT_STYLE, TagInput, place_above_the_status_bar, prompt_width


class RenamePrompt:
    """The `n` prompt over a grid, in the tag prompt's style and place: `Rename tag:` shown above an input taking the old
    tag and the new one. Enter hands the entry to on_enter."""

    def __init__(self, host, status_bar, on_enter):
        self._host = host
        self._status_bar = status_bar
        self.input = TagInput(host)
        self.input.setStyleSheet(TAG_INPUT_STYLE)
        self.input.setCompleter(QCompleter([], self.input))
        self.input.returnPressed.connect(lambda: on_enter(self.input.text()))
        self.input.hide()
        self.label = overlay_label("Rename tag:", host)
        self.label.hide()

    def is_open(self):
        return self.input.isVisible()

    def open(self, tags):
        self.input.clear()
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

    def close(self):
        self.input.hide()
        self.label.hide()
        self._host.setFocus()  # keys go back to the host, not to the hidden input
