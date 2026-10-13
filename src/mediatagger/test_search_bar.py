from PySide6.QtCore import Qt

from mediatagger.search_bar import SearchBar


def test_up_with_no_remembered_searches_keeps_what_was_typed(qtbot, tmp_path):
    bar = SearchBar(tmp_path / "mediatagger" / "state.json")
    qtbot.addWidget(bar)
    bar.open()
    qtbot.keyClicks(bar, "beach")

    qtbot.keyClick(bar, Qt.Key.Key_Up)

    assert bar.text() == "beach"
