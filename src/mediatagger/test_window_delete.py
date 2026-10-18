import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStackedWidget

from mediatagger.grid import TILE_ROLE
from mediatagger.library import Library
from mediatagger.state import remember, state_file
from mediatagger.status_bar import CANT_DELETE_HERE_TEXT, COULDNT_DELETE_TEXT
from mediatagger.test_viewer import SILENT, show_exposed
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, drive_without_a_tag_library_holding_one_image
from mediatagger.test_viewer_open import make_folders
from mediatagger.test_window import shown_status_bar_texts
from mediatagger.test_window_search import search_for
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


def test_del_in_the_grid_of_an_empty_folder_asks_nothing_and_raises_nothing(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    [empty] = make_folders(drive, "Empty")
    remember(state_file(Path.home()), empty, drive)
    questions = []
    window = Window(player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False,
        ask_to_delete=lambda question: questions.append(question))
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    grid = window.findChild(QStackedWidget).currentWidget()

    qtbot.keyClick(grid, Qt.Key.Key_Delete)

    assert (questions, grid.folder) == ([], empty)


def test_del_in_the_viewer_asks_nothing_and_leaves_the_file_on_the_drive(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    questions = []
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False,
        ask_to_delete=lambda question: questions.append(question))
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()

    qtbot.keyClick(viewer, Qt.Key.Key_Delete)

    assert questions == []
    assert (folder / "IMG_1.png").exists()


def test_del_in_a_folder_grid_on_a_drive_without_a_library_asks_nothing_keeps_the_file_and_says_cant_delete_here(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    questions = []
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False,
        ask_to_delete=lambda question: questions.append(question) or True)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert questions == []
    assert (folder / "IMG_1.png").exists()
    assert CANT_DELETE_HERE_TEXT in shown_status_bar_texts(window)


def test_del_on_an_image_its_folder_wont_let_go_of_says_couldnt_delete_and_leaves_its_tags_in_the_library(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    folder.chmod(0o555)
    try:
        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)
    finally:
        folder.chmod(0o755)

    assert (folder / "IMG_1.png").exists()
    assert COULDNT_DELETE_TEXT in shown_status_bar_texts(window)
    assert Library.open(folder.parent).tags(folder / "IMG_1.png") == ["beach"]


def cursor_on_the_folder_tile(qtbot, stack, folder):
    """Backspace from the folder's grid to its parent's, whose cursor lands on the folder's tile."""
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Backspace)
    assert stack.currentWidget().currentIndex().data(TILE_ROLE).path == folder


def test_del_on_a_folder_tile_with_two_files_asks_whether_to_delete_the_folder_and_the_2_files_in_it(qtbot, tmp_path):
    questions = []
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: questions.append(question))
    cursor_on_the_folder_tile(qtbot, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert questions == [f'Delete folder "{folder.name}" and the 2 files in it? It can\'t be undone.']


def test_del_on_a_folder_tile_with_one_file_asks_whether_to_delete_the_folder_and_the_1_file_in_it(qtbot, tmp_path):
    questions = []
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: questions.append(question))
    (folder / "IMG_2.png").unlink()
    cursor_on_the_folder_tile(qtbot, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert questions == [f'Delete folder "{folder.name}" and the 1 file in it? It can\'t be undone.']


def test_del_on_a_folder_tile_holding_only_an_empty_subfolder_asks_whether_to_delete_the_empty_folder(qtbot, tmp_path):
    questions = []
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: questions.append(question))
    for image in folder.iterdir():
        image.unlink()
    (folder / "Later").mkdir()
    cursor_on_the_folder_tile(qtbot, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert questions == [f'Delete empty folder "{folder.name}"?']


def test_the_folder_delete_question_counts_every_file_at_any_depth_leaving_out_hidden_ones_the_drive_adds(qtbot, tmp_path):
    questions = []
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: questions.append(question))
    (folder / "Beach" / "Day 2").mkdir(parents=True)
    for name in ("Beach/clip.mp4", "Beach/Day 2/notes.txt", ".DS_Store", "._IMG_1.png", "Beach/._clip.mp4"):
        (folder / name).write_bytes(b"")
    cursor_on_the_folder_tile(qtbot, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert questions == [f'Delete folder "{folder.name}" and the 4 files in it? It can\'t be undone.']


def test_del_on_a_folder_tile_answered_no_keeps_the_folder_its_files_and_their_tags(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: False)
    cursor_on_the_folder_tile(qtbot, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert sorted(path.name for path in folder.iterdir()) == ["IMG_1.png", "IMG_2.png"]
    assert window.session.library.tags(folder / "IMG_1.png") == ["beach"]


def test_del_on_a_folder_tile_answered_yes_deletes_the_folder_and_everything_in_it_from_the_drive(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    (folder / "Beach").mkdir()
    (folder / "Beach" / "._clip.mp4").write_bytes(b"")
    make_folders(folder.parent, "Videos")
    cursor_on_the_folder_tile(qtbot, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert sorted(path.name for path in folder.parent.iterdir()) == [".mediatagger", "Videos"]


def test_deleting_a_folder_from_a_folder_grid_removes_its_own_tags_and_its_files_tags_from_the_drives_library(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    window.session.library.enter(folder, "holidays")
    cursor_on_the_folder_tile(qtbot, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert Library.open(folder.parent).all_tags() == []


def test_after_deleting_a_folder_tile_the_grid_shows_its_parent_without_it_the_cursor_and_status_bar_on_the_tile_that_took_its_place(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    [videos] = make_folders(folder.parent, "Videos")
    window.session.library.enter(videos, "family")
    cursor_on_the_folder_tile(qtbot, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    grid = stack.currentWidget()
    assert [tile.path for tile in grid.model().tiles] == [videos]
    assert grid.currentIndex().data(TILE_ROLE).path == videos
    assert "family" in shown_status_bar_texts(window)


def test_deleting_a_folder_whose_subfolder_wont_let_go_of_a_file_deletes_the_rest_and_keeps_what_is_left_with_its_tags(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    [stuck] = make_folders(folder, "Stuck")
    (stuck / "IMG_3.png").write_bytes((folder / "IMG_1.png").read_bytes())
    window.session.library.enter(stuck / "IMG_3.png", "sand")
    cursor_on_the_folder_tile(qtbot, stack, folder)
    stuck.chmod(0o555)
    try:
        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)
    finally:
        stuck.chmod(0o755)

    assert sorted(str(path.relative_to(folder)) for path in folder.rglob("*")) == ["Stuck", "Stuck/IMG_3.png"]
    assert Library.open(folder.parent).all_tags() == ["sand"]
    assert COULDNT_DELETE_TEXT in shown_status_bar_texts(window)
    assert stack.currentWidget().currentIndex().data(TILE_ROLE).path == folder


def test_del_on_a_file_in_search_results_asks_nothing_and_leaves_the_file_on_the_drive(qtbot, tmp_path):
    questions = []
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: questions.append(question) or True)
    search_for(qtbot, window, stack, "beach")
    assert stack.currentWidget().currentIndex().data(TILE_ROLE).path == folder / "IMG_1.png"

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert questions == []
    assert (folder / "IMG_1.png").exists()


def answer_the_delete_question_with(qtbot, grid, key):
    """Del on the grid, then the key pressed in whatever modal the window opens; the modal it was, or None."""
    modals = []

    def press_in_whatever_is_open():
        modal = QApplication.activeModalWidget()
        modals.append(modal)
        if modal is not None:  # a key sent to no widget would abort Python
            QTest.keyClick(modal, key)

    QTimer.singleShot(200, press_in_whatever_is_open)
    qtbot.keyClick(grid, Qt.Key.Key_Delete)
    qtbot.waitUntil(lambda: len(modals) == 1)
    return modals[0]


def test_without_a_fake_answer_enter_in_the_windows_delete_question_deletes_the_file(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=None)

    question = answer_the_delete_question_with(qtbot, stack.currentWidget(), Qt.Key.Key_Return)

    assert question is not None
    assert not (folder / "IMG_1.png").exists()


def test_without_a_fake_answer_esc_in_the_windows_delete_question_keeps_the_file(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=None)

    question = answer_the_delete_question_with(qtbot, stack.currentWidget(), Qt.Key.Key_Escape)

    assert question is not None
    assert (folder / "IMG_1.png").exists()


def test_the_windows_delete_question_has_its_delete_button_focused_and_default_and_a_keep_button(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=None)
    buttons = []

    def read_and_keep():
        question = QApplication.activeModalWidget()
        if question is None:
            buttons.append(None)
            return
        default = question.defaultButton()
        buttons.append((default and default.text(), default is not None and question.focusWidget() is default,
            sorted(button.text() for button in question.buttons())))
        question.reject()  # always, or the test would wait on the modal for ever

    QTimer.singleShot(200, read_and_keep)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)
    qtbot.waitUntil(lambda: len(buttons) == 1)

    assert buttons == [("Delete", True, ["Delete", "Keep"])]


def test_deleting_an_image_whose_library_rows_cant_be_removed_still_shows_the_folder_without_it_and_says_tags_couldnt_be_saved(qtbot, tmp_path, monkeypatch):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)

    def drive_pulled(library, path):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(Library, "forget", drive_pulled)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert [tile.path for tile in stack.currentWidget().model().tiles] == [folder / "IMG_2.png"]
    assert "Couldn't save tags — is the drive still connected?" in shown_status_bar_texts(window)


def test_deleting_a_folder_whose_library_rows_cant_be_removed_still_shows_its_parent_without_it_and_says_tags_couldnt_be_saved(qtbot, tmp_path, monkeypatch):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    [videos] = make_folders(folder.parent, "Videos")
    cursor_on_the_folder_tile(qtbot, stack, folder)

    def drive_pulled(library, path):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(Library, "forget_gone", drive_pulled)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert [tile.path for tile in stack.currentWidget().model().tiles] == [videos]
    assert "Couldn't save tags — is the drive still connected?" in shown_status_bar_texts(window)


def test_del_on_a_folder_tile_on_a_drive_without_a_library_asks_nothing_keeps_the_folder_and_says_cant_delete_here(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    questions = []
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False,
        ask_to_delete=lambda question: questions.append(question) or True)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    cursor_on_the_folder_tile(qtbot, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert questions == []
    assert (folder / "IMG_1.png").exists()
    assert CANT_DELETE_HERE_TEXT in shown_status_bar_texts(window)


def test_deleting_a_folder_whose_drive_is_pulled_while_the_question_is_open_says_couldnt_delete(qtbot, tmp_path):
    def pull_the_drive_and_say_yes(question):
        drive.rename(tmp_path / "pulled")
        return True

    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=pull_the_drive_and_say_yes)
    drive = folder.parent
    cursor_on_the_folder_tile(qtbot, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert COULDNT_DELETE_TEXT in shown_status_bar_texts(window)
