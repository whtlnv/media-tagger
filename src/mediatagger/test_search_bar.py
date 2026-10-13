import json

import pytest
from PySide6.QtCore import Qt

from mediatagger.search_bar import SearchBar
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
from mediatagger.test_window import window_showing_the_grid_with_its_cursor_on_its_first_tile
from mediatagger.test_window_search import search_for
from mediatagger.test_window_state import write_state_file


def window_with_the_search_bar_open_over_remembered_searches(qtbot, tmp_path, searches):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    write_state_file(json.dumps({"searches": searches}))
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)
    return window, stack


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


UP, DOWN = Qt.Key.Key_Up, Qt.Key.Key_Down


@pytest.mark.parametrize("searches, typed, keys, shown", [
    pytest.param(["family", "beach -sunset"], "moun", [UP], "beach -sunset", id="up replaces its text with the most recent search"),
    pytest.param(["family", "beach -sunset", "mountain"], "", [UP, UP], "beach -sunset", id="each further up recalls the next older search"),
    pytest.param(["family", "mountain"], "", [UP, UP, UP], "family", id="up at the oldest remembered search keeps it"),
    pytest.param(["family", "beach -sunset", "mountain"], "", [UP, UP, UP, DOWN], "beach -sunset", id="down after up recalls the next newer search"),
    pytest.param(["family", "beach -sunset", "mountain"], "", [UP, DOWN], "", id="down past the newest search leaves it empty"),
])
def test_up_and_down_in_the_search_bar_recall_remembered_searches(qtbot, tmp_path, searches, typed, keys, shown):
    window, _ = window_with_the_search_bar_open_over_remembered_searches(qtbot, tmp_path, searches)
    qtbot.keyClicks(window.search_bar, typed)

    for key in keys:
        qtbot.keyClick(window.search_bar, key)

    assert window.search_bar.text() == shown


def test_a_search_run_in_the_window_is_recalled_by_up_when_the_search_bar_next_opens(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window, stack = window_showing_the_grid_with_its_cursor_on_its_first_tile(qtbot, drive, folder)
    search_for(qtbot, window, stack, "beach -sunset")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Slash)

    qtbot.keyClick(window.search_bar, Qt.Key.Key_Up)

    assert window.search_bar.text() == "beach -sunset"


def test_up_in_a_reopened_search_bar_starts_again_from_the_most_recent_search(qtbot, tmp_path):
    window, stack = window_with_the_search_bar_open_over_remembered_searches(qtbot, tmp_path, ["family", "beach -sunset", "mountain"])
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


def test_the_search_bar_is_drawn_in_the_status_bars_font_size(qtbot, tmp_path):
    from mediatagger.status_bar import overlay_label

    bar = SearchBar(tmp_path / "mediatagger" / "state.json")
    label = overlay_label("", None)
    qtbot.addWidget(bar)
    qtbot.addWidget(label)

    bar.ensurePolished()
    label.ensurePolished()

    assert bar.font().pixelSize() == label.font().pixelSize()
