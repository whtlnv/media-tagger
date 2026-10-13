import json

from PySide6.QtCore import Qt

from mediatagger.search_bar import SearchBar
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
from mediatagger.test_window import window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.test_window_search import search_for
from mediatagger.test_window_state import write_state_file


def test_up_with_no_remembered_searches_keeps_what_was_typed(qtbot, tmp_path):
    bar = SearchBar(tmp_path / "mediatagger" / "state.json")
    qtbot.addWidget(bar)
    bar.open()
    qtbot.keyClicks(bar, "beach")

    qtbot.keyClick(bar, Qt.Key.Key_Up)

    assert bar.text() == "beach"


def test_down_before_any_up_keeps_what_was_typed(qtbot, tmp_path):
    state = tmp_path / "mediatagger" / "state.json"
    state.parent.mkdir()
    state.write_text('{"searches": ["family", "mountain"]}')
    bar = SearchBar(state)
    qtbot.addWidget(bar)
    bar.open()
    qtbot.keyClicks(bar, "beach")

    qtbot.keyClick(bar, Qt.Key.Key_Down)

    assert bar.text() == "beach"


def test_up_in_the_search_bar_replaces_its_text_with_the_most_recent_search(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_state_file(json.dumps({"searches": ["family", "beach -sunset"]}))
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    qtbot.keyClicks(window.search_bar, "moun")

    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)

    assert window.search_bar.text() == "beach -sunset"


def test_each_further_up_in_the_search_bar_recalls_the_next_older_search(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_state_file(json.dumps({"searches": ["family", "beach -sunset", "mountain"]}))
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)

    assert window.search_bar.text() == "beach -sunset"


def test_up_at_the_oldest_remembered_search_keeps_it_in_the_search_bar(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_state_file(json.dumps({"searches": ["family", "mountain"]}))
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)

    assert window.search_bar.text() == "family"


def test_down_in_the_search_bar_after_up_recalls_the_next_newer_search(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_state_file(json.dumps({"searches": ["family", "beach -sunset", "mountain"]}))
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)

    qtbot.keyClick(window.search_bar, Qt.Key.Key_Down)

    assert window.search_bar.text() == "beach -sunset"


def test_down_past_the_newest_search_leaves_the_search_bar_empty(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_state_file(json.dumps({"searches": ["family", "beach -sunset", "mountain"]}))
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)

    qtbot.keyClick(window.search_bar, Qt.Key.Key_Down)

    assert window.search_bar.text() == ""


def test_a_search_run_in_the_window_is_recalled_by_up_when_the_search_bar_next_opens(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach -sunset")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)

    assert window.search_bar.text() == "beach -sunset"


def test_up_in_a_reopened_search_bar_starts_again_from_the_most_recent_search(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_state_file(json.dumps({"searches": ["family", "beach -sunset", "mountain"]}))
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)
    qtbot.keyClick(window.search_bar, Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)

    assert window.search_bar.text() == "mountain"


def test_the_search_bar_opens_empty_after_an_earlier_search(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    assert window.search_bar.text() == ""
