from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget

from mediatagger.grid import TILE_ROLE
from mediatagger.library import Library
from mediatagger.test_viewer import SILENT, show_exposed
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
from mediatagger.test_window import shown_status_bar_texts
from mediatagger.window import Window


def grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete):
    """The window's grid of Photos (IMG_1.png tagged beach, IMG_2.png) on a drive with a library, its cursor on IMG_1.png."""
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    (folder / "IMG_2.png").write_bytes((folder / "IMG_1.png").read_bytes())
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
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


def test_del_on_an_image_tile_in_a_folder_grid_asks_whether_to_delete_it_naming_it_and_saying_it_cant_be_undone(qtbot, tmp_path):
    questions = []
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: questions.append(question))

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert questions == ['Delete "IMG_1.png"? It can\'t be undone.']


def test_del_on_an_image_tile_in_a_folder_grid_answered_no_keeps_the_file_and_its_tags(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: False)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert (folder / "IMG_1.png").exists()
    assert window.session.library.tags(folder / "IMG_1.png") == ["beach"]


def test_deleting_an_image_tagged_beach_from_a_folder_grid_removes_its_tags_from_the_drives_library(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert Library.open(folder.parent).all_tags() == []


def test_after_deleting_the_first_of_two_images_the_folder_grid_shows_only_the_second_with_the_cursor_on_it(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    grid = stack.currentWidget()
    assert [tile.path for tile in grid.model().tiles] == [folder / "IMG_2.png"]
    assert grid.currentIndex().data(TILE_ROLE).path == folder / "IMG_2.png"


def test_after_deleting_the_last_of_two_images_the_folder_grids_cursor_is_on_the_first(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert stack.currentWidget().currentIndex().data(TILE_ROLE).path == folder / "IMG_1.png"


def test_after_deleting_an_image_the_status_bar_shows_the_tags_of_the_image_now_under_the_cursor(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    window.session.library.enter(folder / "IMG_2.png", "family")

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert "family" in shown_status_bar_texts(window)
    assert "beach" not in shown_status_bar_texts(window)
