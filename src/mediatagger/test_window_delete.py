from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget

from mediatagger.test_viewer import SILENT, show_exposed
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
from mediatagger.window import Window


def grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete):
    """The window's grid of Photos (IMG_1.png, IMG_2.png) on a drive with a library, its cursor on IMG_1.png."""
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    (folder / "IMG_2.png").write_bytes((folder / "IMG_1.png").read_bytes())
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False,
        ask_to_delete=ask_to_delete)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Left)
    return window, stack, folder


def test_del_on_an_image_tile_in_a_folder_grid_answered_yes_deletes_the_file_from_the_drive(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert not (folder / "IMG_1.png").exists()
    assert (folder / "IMG_2.png").exists()
