import sqlite3
import time

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QApplication

from mediatagger.library import Library
from mediatagger.test_video import wait_until_playing
from mediatagger.test_viewer import light_theme, make_image, make_surface_ready
from mediatagger.test_viewer_library import (
    drive_with_a_tag_library_holding_one_clip, drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, make_tag_library_drive, shown_viewer_on_drive, shown_viewer_on_drives, status_bar_texts, visible_tag_prompt_texts,
    visible_tag_prompts,
)
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders
from mediatagger.viewer import COULDNT_SAVE_TAGS_TEXT


def visible_suggestion_lists(viewer):
    return [widget for widget in QApplication.allWidgets() if isinstance(widget, QAbstractItemView) and widget.isVisible()]


def listed(suggestions):
    model = suggestions.model()
    return [model.index(row, 0).data() for row in range(model.rowCount())]


def type_in_tag_prompt(qtbot, viewer, text):
    qtbot.keyClick(viewer, Qt.Key.Key_T)
    [prompt] = visible_tag_prompts(viewer)
    qtbot.keyClicks(prompt, text)


def shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, tags):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", tags)
    return drive, folder, shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)


def test_in_the_tag_prompt_on_a_drive_whose_library_has_beach_and_bird_typing_b_shows_a_suggestion_popup_listing_beach_and_bird(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "beach bird")

    type_in_tag_prompt(qtbot, viewer, "b")

    [suggestions] = visible_suggestion_lists(viewer)
    assert sorted(listed(suggestions)) == ["beach", "bird"]


def test_in_the_tag_prompt_on_a_drive_whose_library_has_no_tags_yet_typing_b_shows_no_suggestion_popup(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    type_in_tag_prompt(qtbot, viewer, "b")

    assert visible_suggestion_lists(viewer) == []


def test_in_the_tag_prompt_on_a_drive_whose_library_has_beach_and_bird_typing_be_lists_beach_and_not_bird(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "beach bird")

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
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "beach bird")

    type_in_tag_prompt(qtbot, viewer, "BE")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["beach"]


def test_suggestions_complete_the_last_space_separated_word_typing_beach_fam_with_family_in_the_library_lists_family(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "beach family")

    type_in_tag_prompt(qtbot, viewer, "beach fam")

    [suggestions] = visible_suggestion_lists(viewer)
    assert listed(suggestions) == ["family"]


def test_typing_a_namespace_prefix_people_colon_lists_every_tag_under_it_at_any_depth_and_not_place_mexico(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "people:ana people:luis:jr place:mexico")

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
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "beach bird")

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
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "beach bird")
    type_in_tag_prompt(qtbot, viewer, "b")
    [suggestions] = visible_suggestion_lists(viewer)
    first, second = listed(suggestions)

    qtbot.keyClick(suggestions, Qt.Key.Key_Down)
    qtbot.keyClick(suggestions, Qt.Key.Key_Down)
    highlighted_after_down_twice = suggestions.currentIndex().data()
    qtbot.keyClick(suggestions, Qt.Key.Key_Up)

    assert (highlighted_after_down_twice, suggestions.currentIndex().data()) == (second, first)


def test_tab_accepts_the_highlighted_suggestion_replacing_only_the_word_being_typed_beach_fam_down_tab_leaves_beach_family_and_closes_the_popup(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "beach family")
    type_in_tag_prompt(qtbot, viewer, "beach fam")
    [suggestions] = visible_suggestion_lists(viewer)

    qtbot.keyClick(suggestions, Qt.Key.Key_Down)
    qtbot.keyClick(suggestions, Qt.Key.Key_Tab)

    [prompt] = visible_tag_prompts(viewer)
    assert (prompt.text(), visible_suggestion_lists(viewer)) == ("beach family", [])


def test_enter_accepts_the_highlighted_suggestion_without_saving_beach_fam_down_enter_leaves_beach_family_in_the_open_prompt_and_the_items_tags_unchanged(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "beach family")
    type_in_tag_prompt(qtbot, viewer, "beach fam")
    [suggestions] = visible_suggestion_lists(viewer)

    qtbot.keyClick(suggestions, Qt.Key.Key_Down)
    qtbot.keyClick(suggestions, Qt.Key.Key_Return)

    assert (visible_tag_prompt_texts(viewer), Library.open(drive).tags(folder / "IMG_1.png")) == (["beach family"], [])


def test_accepting_a_removal_suggestion_keeps_the_minus_on_an_item_tagged_sunset_minus_s_down_tab_leaves_minus_sunset_in_the_prompt(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "sunset")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    type_in_tag_prompt(qtbot, viewer, "-s")
    [suggestions] = visible_suggestion_lists(viewer)

    qtbot.keyClick(suggestions, Qt.Key.Key_Down)
    qtbot.keyClick(suggestions, Qt.Key.Key_Tab)

    [prompt] = visible_tag_prompts(viewer)
    assert prompt.text() == "-sunset"


def test_esc_with_the_suggestion_popup_open_closes_only_the_popup_leaving_the_prompt_open_with_its_text_and_the_viewer_running(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "beach family")
    type_in_tag_prompt(qtbot, viewer, "beach fam")
    [suggestions] = visible_suggestion_lists(viewer)

    qtbot.keyClick(suggestions, Qt.Key.Key_Escape)

    assert (visible_suggestion_lists(viewer), visible_tag_prompt_texts(viewer), viewer.isVisible()) == ([], ["beach fam"], True)


def test_accepting_a_suggestion_for_the_only_word_in_the_prompt_leaves_no_leading_space_fam_down_tab_leaves_exactly_family(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "family")
    type_in_tag_prompt(qtbot, viewer, "fam")
    [suggestions] = visible_suggestion_lists(viewer)

    qtbot.keyClick(suggestions, Qt.Key.Key_Down)
    qtbot.keyClick(suggestions, Qt.Key.Key_Tab)

    assert visible_tag_prompt_texts(viewer) == ["family"]


def test_esc_after_the_suggestion_popup_has_been_closed_cancels_the_prompt_leaving_the_items_tags_unchanged(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    type_in_tag_prompt(qtbot, viewer, "fam")
    [suggestions] = visible_suggestion_lists(viewer)
    qtbot.keyClick(suggestions, Qt.Key.Key_Escape)

    qtbot.keyClick(viewer.focusWidget(), Qt.Key.Key_Escape)

    assert (visible_tag_prompt_texts(viewer), Library.open(drive).tags(folder / "IMG_1.png"), viewer.isVisible()) == ([], ["beach"], True)


def test_enter_with_no_suggestion_popup_showing_saves_the_prompts_text_beach_fam_esc_enter_adds_beach_and_fam_to_the_item(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "family")
    type_in_tag_prompt(qtbot, viewer, "beach fam")
    [suggestions] = visible_suggestion_lists(viewer)
    qtbot.keyClick(suggestions, Qt.Key.Key_Escape)

    qtbot.keyClick(viewer.focusWidget(), Qt.Key.Key_Return)

    assert (visible_tag_prompt_texts(viewer), sorted(Library.open(drive).tags(folder / "IMG_1.png"))) == ([], ["beach", "fam"])


def test_on_a_paused_video_with_the_suggestion_popup_open_down_twice_and_up_highlight_the_first_suggestion_and_do_not_seek_the_video(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=60)
    make_image(folder / "IMG_2.png", "red")
    Library.open(drive).enter(folder / "IMG_2.png", "beach bird")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    wait_until_playing(engine)
    qtbot.keyClick(viewer, Qt.Key.Key_P)
    engine.time_pos = 20
    engine.wait_for_property("time-pos", lambda time_pos: time_pos == pytest.approx(20, abs=1), timeout=5)
    type_in_tag_prompt(qtbot, viewer, "b")
    [suggestions] = visible_suggestion_lists(viewer)
    first, second = listed(suggestions)

    for key in (Qt.Key.Key_Down, Qt.Key.Key_Down, Qt.Key.Key_Up):
        qtbot.keyClick(suggestions, key)
    qtbot.wait(300)  # mpv seeks asynchronously, so give a stray seek time to land

    assert (suggestions.currentIndex().data(), engine.time_pos) == (first, pytest.approx(20, abs=1))


def test_the_suggestion_popup_over_a_white_image_shows_light_text_on_a_dark_background_as_the_overlays_do(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "white")
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach bird")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    light_theme(viewer)

    type_in_tag_prompt(qtbot, viewer, "b")

    [suggestions] = visible_suggestion_lists(viewer)
    frame = suggestions.viewport().grab().toImage()
    ratio = frame.devicePixelRatio()
    def colour_at(x, y):
        return frame.pixelColor(int(x * ratio), int(y * ratio))
    first_row = suggestions.visualRect(suggestions.model().index(0, 0))
    colours = [colour_at(x, y) for x in range(first_row.left(), first_row.right()) for y in range(first_row.top(), first_row.bottom())]
    background = colour_at(first_row.right() - 4, first_row.center().y())
    assert background.lightness() < 100  # dark background
    assert any(colour.lightness() > 200 and colour.saturation() < 40 for colour in colours)  # light text


def test_the_suggestion_popup_opens_above_the_prompt_and_lies_entirely_inside_the_window_even_with_more_suggestions_than_fit_below_the_prompt(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, " ".join(f"bird{number}" for number in range(30)))

    type_in_tag_prompt(qtbot, viewer, "b")

    [suggestions] = visible_suggestion_lists(viewer)
    [prompt] = visible_tag_prompts(viewer)
    popup = suggestions.window().frameGeometry()
    window = viewer.frameGeometry()
    prompt_top = prompt.mapToGlobal(prompt.rect().topLeft()).y()
    assert (popup.bottom() < prompt_top, window.contains(popup)) == (True, True)


def test_with_5000_tags_in_the_library_each_keystroke_after_the_popup_opens_updates_the_suggestions_in_under_50_ms(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, " ".join(f"tag{number:04}" for number in range(5000)))
    type_in_tag_prompt(qtbot, viewer, "")
    [prompt] = visible_tag_prompts(viewer)

    qtbot.keyClick(prompt, "t")  # the first keystroke also builds and shows the popup, a one-off cost
    keystroke_times = []
    for key in "ag12":
        started = time.perf_counter()
        qtbot.keyClick(prompt, key)
        keystroke_times.append(time.perf_counter() - started)

    [suggestions] = visible_suggestion_lists(viewer)
    assert (max(keystroke_times) < 0.050, listed(suggestions)[:2]) == (True, ["tag1200", "tag1201"])


@pytest.mark.parametrize("drive_error", [sqlite3.OperationalError("disk I/O error"), OSError(5, "Input/output error")], ids=["sqlite_error", "os_error"])
def test_when_saving_the_prompt_fails_with_a_drive_error_the_prompt_stays_open_with_its_text_and_the_status_bar_says_it_couldnt_save_tags(qtbot, tmp_path, monkeypatch, drive_error):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    def enter_on_an_unplugged_drive(self, path, text):
        raise drive_error

    monkeypatch.setattr(Library, "enter", enter_on_an_unplugged_drive)

    enter_in_tag_prompt(qtbot, viewer, "beach")

    assert (visible_tag_prompt_texts(viewer), COULDNT_SAVE_TAGS_TEXT in status_bar_texts(viewer)) == (["beach"], True)


def test_enter_with_the_popup_showing_but_no_suggestion_highlighted_saves_the_prompts_text_typing_sunset_then_enter_tags_the_item_sunset(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "sunset")
    type_in_tag_prompt(qtbot, viewer, "sunset")
    [suggestions] = visible_suggestion_lists(viewer)

    qtbot.keyClick(suggestions, Qt.Key.Key_Return)

    assert (visible_tag_prompt_texts(viewer), Library.open(drive).tags(folder / "IMG_1.png")) == ([], ["sunset"])


def test_tab_with_the_popup_showing_but_no_suggestion_highlighted_leaves_the_prompts_text_as_typed(qtbot, tmp_path):
    drive, folder, viewer = shown_viewer_on_a_drive_whose_library_has(qtbot, tmp_path, "beach bird")
    type_in_tag_prompt(qtbot, viewer, "b")
    [suggestions] = visible_suggestion_lists(viewer)

    qtbot.keyClick(suggestions, Qt.Key.Key_Tab)

    assert visible_tag_prompt_texts(viewer) == ["b"]
