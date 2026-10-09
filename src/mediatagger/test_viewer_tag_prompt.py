from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QApplication

from mediatagger.library import Library
from mediatagger.test_viewer import make_image
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, shown_viewer_on_drive, visible_tag_prompts


def visible_suggestion_lists(viewer):
    return [widget for widget in QApplication.allWidgets() if isinstance(widget, QAbstractItemView) and widget.isVisible()]


def listed(suggestions):
    model = suggestions.model()
    return [model.index(row, 0).data() for row in range(model.rowCount())]


def type_in_tag_prompt(qtbot, viewer, text):
    qtbot.keyClick(viewer, Qt.Key.Key_T)
    [prompt] = visible_tag_prompts(viewer)
    qtbot.keyClicks(prompt, text)


def test_in_the_tag_prompt_on_a_drive_whose_library_has_beach_and_bird_typing_b_shows_a_suggestion_popup_listing_beach_and_bird(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach bird")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "b")

    [suggestions] = visible_suggestion_lists(viewer)
    assert sorted(listed(suggestions)) == ["beach", "bird"]


def test_in_the_tag_prompt_on_a_drive_whose_library_has_no_tags_yet_typing_b_shows_no_suggestion_popup(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "b")

    assert visible_suggestion_lists(viewer) == []


def test_in_the_tag_prompt_on_a_drive_whose_library_has_beach_and_bird_typing_be_lists_beach_and_not_bird(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach bird")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "be")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["beach"]
