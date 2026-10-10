from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget

from mediatagger.grid import Grid

from mediatagger.test_viewer import SILENT, make_image
from mediatagger.viewer import Viewer
from mediatagger.window import Window


def test_the_window_opened_on_a_folder_path_shows_the_slideshow_of_that_folder_at_its_first_item(qtbot, tmp_path):
    make_image(tmp_path / "b.jpg", "blue")
    make_image(tmp_path / "a.jpg", "red")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)

    shown = window.findChild(QStackedWidget).currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == tmp_path / "a.jpg"


def test_in_the_windows_viewer_esc_shows_the_grid_of_the_current_items_folder_with_the_cursor_on_that_item(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(Qt.ItemDataRole.DisplayRole) == "a.jpg"


def test_in_the_windows_viewer_esc_after_stepping_to_the_second_item_puts_the_grid_cursor_on_the_second_item(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(Qt.ItemDataRole.DisplayRole) == "b.jpg"
