from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QApplication

from mediatagger.library import Library
from mediatagger.test_viewer import make_image
from mediatagger.test_viewer_library import (
    drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, make_tag_library_drive, shown_viewer_on_drive, shown_viewer_on_drives, visible_tag_prompt_texts, visible_tag_prompts,
)
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders


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


def test_suggestions_are_ordered_by_item_count_with_bird_on_3_items_and_beach_on_1_typing_b_lists_bird_above_beach(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    for name in ("IMG_2.png", "IMG_3.png", "IMG_4.png"):
        make_image(folder / name, "blue")
    library = Library.open(drive)
    library.enter(folder / "IMG_2.png", "bird beach")
    library.enter(folder / "IMG_3.png", "bird")
    library.enter(folder / "IMG_4.png", "bird")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "b")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["bird", "beach"]


def test_suggestions_are_ordered_by_item_count_with_beach_on_3_items_and_bird_on_1_typing_b_lists_beach_above_bird(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    for name in ("IMG_2.png", "IMG_3.png", "IMG_4.png"):
        make_image(folder / name, "blue")
    library = Library.open(drive)
    library.enter(folder / "IMG_2.png", "beach bird")
    library.enter(folder / "IMG_3.png", "beach")
    library.enter(folder / "IMG_4.png", "beach")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "b")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["beach", "bird"]


def test_suggestions_with_the_same_item_count_are_listed_alphabetically_with_bird_and_beach_on_2_items_each_typing_b_lists_beach_above_bird(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    for name in ("IMG_2.png", "IMG_3.png", "IMG_4.png"):
        make_image(folder / name, "blue")
    library = Library.open(drive)
    library.enter(folder / "IMG_2.png", "bird")
    library.enter(folder / "IMG_3.png", "bird beach")
    library.enter(folder / "IMG_4.png", "beach")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "b")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["beach", "bird"]


def test_suggestion_matching_ignores_case_typing_upper_case_be_lists_beach(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach bird")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "BE")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["beach"]


def test_suggestions_complete_the_last_space_separated_word_typing_beach_fam_with_family_in_the_library_lists_family(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "beach fam")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["family"]


def test_typing_a_namespace_prefix_people_colon_lists_every_tag_under_it_at_any_depth_and_not_place_mexico(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "people:ana people:luis:jr place:mexico")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "people:")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["people:ana", "people:luis:jr"]


def test_tags_the_viewed_item_already_has_are_not_suggested_on_an_item_tagged_sunset_with_summer_in_the_library_typing_s_lists_summer_and_not_sunset(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    library = Library.open(drive)
    library.enter(folder / "IMG_1.png", "sunset")
    library.enter(folder / "IMG_2.png", "summer")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "s")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["summer"]


def test_a_word_starting_with_minus_suggests_from_the_viewed_items_own_tags_on_an_item_tagged_sunset_with_summer_in_the_library_typing_minus_s_lists_sunset_and_not_summer(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    library = Library.open(drive)
    library.enter(folder / "IMG_1.png", "sunset")
    library.enter(folder / "IMG_2.png", "summer")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "-s")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["sunset"]


def test_words_already_entered_in_the_prompt_are_not_suggested_again_typing_beach_b_lists_bird_and_not_beach(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach bird")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "beach b")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["bird"]


def test_suggestions_come_from_the_current_drives_library_after_dropping_a_folder_from_a_second_drive_with_only_zebra_typing_b_shows_no_popup_and_z_lists_zebra(qtbot, tmp_path):
    first_drive, viewed = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(first_drive).enter(viewed / "IMG_1.png", "beach bird")
    second_drive = make_tag_library_drive(tmp_path / "BACKUP")
    [dropped] = make_folders(second_drive, "Photos")
    make_image(dropped / "IMG_1.png", "green")
    make_image(dropped / "IMG_2.png", "blue")
    Library.open(second_drive).enter(dropped / "IMG_2.png", "zebra")
    viewer = shown_viewer_on_drives(qtbot, viewed, (first_drive, second_drive), lambda question: False)
    drag_and_drop_onto(viewer, dropped)

    type_in_tag_prompt(qtbot, viewer, "b")
    assert visible_suggestion_lists(viewer) == []

    [prompt] = visible_tag_prompts(viewer)
    qtbot.keyClick(prompt, Qt.Key.Key_Backspace)
    qtbot.keyClicks(prompt, "z")
    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["zebra"]


def test_a_tag_saved_from_the_prompt_is_suggested_the_next_time_the_prompt_opens_after_saving_zebra_on_one_item_typing_z_on_the_next_lists_zebra(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    enter_in_tag_prompt(qtbot, viewer, "zebra")
    qtbot.keyClick(viewer, Qt.Key.Key_Right)

    type_in_tag_prompt(qtbot, viewer, "z")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["zebra"]


def test_in_the_suggestion_popup_down_twice_highlights_the_second_suggestion_and_up_then_highlights_the_first(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach bird")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    type_in_tag_prompt(qtbot, viewer, "b")
    [suggestions] = visible_suggestion_lists(viewer)
    first, second = listed(suggestions)

    qtbot.keyClick(suggestions, Qt.Key.Key_Down)
    qtbot.keyClick(suggestions, Qt.Key.Key_Down)
    highlighted_after_down_twice = suggestions.currentIndex().data()
    qtbot.keyClick(suggestions, Qt.Key.Key_Up)

    assert (highlighted_after_down_twice, suggestions.currentIndex().data()) == (second, first)


def test_tab_accepts_the_highlighted_suggestion_replacing_only_the_word_being_typed_beach_fam_down_tab_leaves_beach_family_and_closes_the_popup(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    type_in_tag_prompt(qtbot, viewer, "beach fam")
    [suggestions] = visible_suggestion_lists(viewer)

    qtbot.keyClick(suggestions, Qt.Key.Key_Down)
    qtbot.keyClick(suggestions, Qt.Key.Key_Tab)

    [prompt] = visible_tag_prompts(viewer)
    assert (prompt.text(), visible_suggestion_lists(viewer)) == ("beach family", [])


def test_enter_accepts_the_highlighted_suggestion_without_saving_beach_fam_down_enter_leaves_beach_family_in_the_open_prompt_and_the_items_tags_unchanged(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    type_in_tag_prompt(qtbot, viewer, "beach fam")
    [suggestions] = visible_suggestion_lists(viewer)

    qtbot.keyClick(suggestions, Qt.Key.Key_Down)
    qtbot.keyClick(suggestions, Qt.Key.Key_Return)

    assert (visible_tag_prompt_texts(viewer), Library.open(drive).tags(folder / "IMG_1.png")) == (["beach family"], [])
