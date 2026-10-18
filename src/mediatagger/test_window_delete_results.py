from PySide6.QtCore import Qt

from mediatagger.grid import TILE_ROLE
from mediatagger.library import Library
from mediatagger.test_viewer_open import make_folders
from mediatagger.test_window import shown_status_bar_texts
from mediatagger.test_window_delete import buttons_of_the_question_del_opens, grid_of_a_folder_with_two_images
from mediatagger.test_window_search import search_for


def test_del_on_a_file_in_search_results_answered_yes_deletes_it_from_the_drive_and_its_tags_from_the_library(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    search_for(qtbot, window, stack, "beach")
    assert stack.currentWidget().currentIndex().data(TILE_ROLE).path == folder / "IMG_1.png"

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert not (folder / "IMG_1.png").exists()
    assert Library.open(folder.parent).all_tags() == []


def results_of_beach_holding_both_images(qtbot, window, stack, folder):
    """Search results for beach: IMG_1.png and IMG_2.png (tagged beach and family), the cursor on IMG_1.png; untagged
    IMG_3.png lies beside them in their folder."""
    (folder / "IMG_3.png").write_bytes((folder / "IMG_1.png").read_bytes())
    window.session.library.enter(folder / "IMG_2.png", "beach family")
    search_for(qtbot, window, stack, "beach")
    assert [tile.path for tile in stack.currentWidget().model().tiles] == [folder / "IMG_1.png", folder / "IMG_2.png"]


def test_after_deleting_a_file_from_search_results_the_same_search_shows_without_it_the_cursor_and_tags_on_the_result_that_took_its_place(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    results_of_beach_holding_both_images(qtbot, window, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    results = stack.currentWidget()
    assert [tile.path for tile in results.model().tiles] == [folder / "IMG_2.png"]
    assert results.currentIndex().data(TILE_ROLE).path == folder / "IMG_2.png"
    assert (window.breadcrumb.isVisible(), window.breadcrumb.text()) == (True, "Search: beach")
    assert "beach family" in shown_status_bar_texts(window)


def test_after_deleting_the_last_search_result_the_cursor_is_on_the_result_before_it(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    results_of_beach_holding_both_images(qtbot, window, stack, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert [tile.path for tile in stack.currentWidget().model().tiles] == [folder / "IMG_1.png"]
    assert stack.currentWidget().currentIndex().data(TILE_ROLE).path == folder / "IMG_1.png"


def test_esc_from_search_results_after_deleting_a_result_from_the_folder_searched_from_shows_that_folder_without_it(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    results_of_beach_holding_both_images(qtbot, window, stack, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    grid = stack.currentWidget()
    assert (grid.folder, [tile.path for tile in grid.model().tiles]) == (folder, [folder / "IMG_2.png", folder / "IMG_3.png"])


def test_back_from_a_slideshow_opened_from_search_results_after_a_delete_the_cursor_is_on_the_slideshows_file(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    (folder / "IMG_3.png").write_bytes((folder / "IMG_1.png").read_bytes())
    window.session.library.enter(folder / "IMG_2.png", "beach")
    window.session.library.enter(folder / "IMG_3.png", "beach")
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Space)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    results = stack.currentWidget()
    assert [tile.path for tile in results.model().tiles] == [folder / "IMG_2.png", folder / "IMG_3.png"]
    assert results.currentIndex().data(TILE_ROLE).path == folder / "IMG_3.png"


def results_of_holidays_holding_two_folders(qtbot, window, stack, folder):
    """Search results for holidays: the image folder and a Videos folder beside it, both tagged holidays, the cursor on
    the image folder."""
    [videos] = make_folders(folder.parent, "Videos")
    window.session.library.enter(folder, "holidays")
    window.session.library.enter(videos, "holidays")
    search_for(qtbot, window, stack, "holidays")
    assert [tile.path for tile in stack.currentWidget().model().tiles] == [folder, videos]
    return videos


def test_del_on_a_folder_in_search_results_answered_yes_deletes_it_and_its_tags_and_it_leaves_the_results(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    videos = results_of_holidays_holding_two_folders(qtbot, window, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert not folder.exists()
    assert Library.open(folder.parent).all_tags() == ["holidays"]
    results = stack.currentWidget()
    assert [tile.path for tile in results.model().tiles] == [videos]
    assert results.currentIndex().data(TILE_ROLE).path == videos


def test_esc_from_search_results_after_deleting_the_folder_searched_from_shows_its_parent_without_it(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    videos = results_of_holidays_holding_two_folders(qtbot, window, stack, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    grid = stack.currentWidget()
    assert (grid.folder, [tile.path for tile in grid.model().tiles]) == (folder.parent, [videos])
    assert grid.currentIndex().data(TILE_ROLE).path == videos


def results_of_beach_with_the_cursor_on_a_missing_image(qtbot, window, stack, folder):
    """Search results for beach: IMG_1.png and IMG_2.png, gone from the drive since it was tagged; the cursor on IMG_2.png."""
    window.session.library.enter(folder / "IMG_2.png", "beach sand")
    (folder / "IMG_2.png").unlink()
    search_for(qtbot, window, stack, "beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)
    assert stack.currentWidget().currentIndex().data(TILE_ROLE).path == folder / "IMG_2.png"


def test_del_on_a_missing_search_result_asks_whether_to_forget_it_saying_its_tags_are_removed(qtbot, tmp_path):
    questions = []
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: questions.append(question))
    results_of_beach_with_the_cursor_on_a_missing_image(qtbot, window, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert questions == ['Forget "IMG_2.png"? Its tags are removed.']


def test_a_missing_search_result_answered_yes_loses_its_tags_and_leaves_the_results(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    results_of_beach_with_the_cursor_on_a_missing_image(qtbot, window, stack, folder)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    assert Library.open(folder.parent).all_tags() == ["beach"]
    results = stack.currentWidget()
    assert [tile.path for tile in results.model().tiles] == [folder / "IMG_1.png"]
    assert results.currentIndex().data(TILE_ROLE).path == folder / "IMG_1.png"


def test_esc_from_search_results_after_deleting_a_folder_above_the_one_searched_from_shows_the_nearest_folder_left(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    [beach] = make_folders(folder, "Beach")
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Backspace)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)  # into the image folder, its cursor on Beach
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)  # into Beach
    assert stack.currentWidget().folder == beach
    videos = results_of_holidays_holding_two_folders(qtbot, window, stack, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    grid = stack.currentWidget()
    assert (grid.folder, [tile.path for tile in grid.model().tiles]) == (folder.parent, [videos])


def test_a_folder_picked_from_search_results_after_a_delete_goes_back_to_its_own_grid_on_esc(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=lambda question: True)
    results_of_beach_holding_both_images(qtbot, window, stack, folder)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)  # back to the results, from a slideshow over them
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Delete)
    [picked] = make_folders(folder.parent, "Picked")
    (picked / "IMG_9.png").write_bytes((folder / "IMG_2.png").read_bytes())
    window.viewer.folder_picker = lambda: picked
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_O)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert stack.currentWidget().folder == picked


def test_the_windows_question_for_a_missing_search_result_has_its_forget_button_focused_and_default_and_a_keep_button(qtbot, tmp_path):
    window, stack, folder = grid_of_a_folder_with_two_images(qtbot, tmp_path, ask_to_delete=None)
    results_of_beach_with_the_cursor_on_a_missing_image(qtbot, window, stack, folder)

    assert buttons_of_the_question_del_opens(qtbot, stack.currentWidget()) == ("Forget", True, ["Forget", "Keep"])
    assert window.session.library.tags(folder / "IMG_2.png") == ["beach", "sand"]
