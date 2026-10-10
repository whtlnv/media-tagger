from PySide6.QtWidgets import QStackedWidget

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
