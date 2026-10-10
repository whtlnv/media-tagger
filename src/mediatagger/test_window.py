import errno
import os
from datetime import datetime, timezone

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QLabel, QStackedWidget

from mediatagger.drive_session import BACKUP_FAILED_TEXT
from mediatagger.grid import TILE_ROLE, Grid
from mediatagger.library import Library
from mediatagger.status_bar import READ_ONLY_STATUS_TEXT, StatusBar

from mediatagger.test_video import make_clip
from mediatagger.test_viewer import SILENT, make_image, make_surface_ready, show_exposed, wait_until_loaded
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, made_read_only, visible_tag_prompts
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders
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


def test_in_the_windows_viewer_on_a_playing_video_esc_to_the_grid_stops_the_video(qtbot, tmp_path):
    clip = make_clip(tmp_path / "a.mp4")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()
    make_surface_ready(viewer)
    wait_until_loaded(viewer.video_player.engine, clip)

    qtbot.keyClick(viewer, Qt.Key.Key_Escape)

    assert viewer.video_player.engine.path is None


def test_in_the_windows_viewer_with_the_tag_prompt_open_esc_closes_the_prompt_and_stays_in_the_viewer(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    viewer = stack.currentWidget()
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    qtbot.keyClick(viewer.focusWidget(), Qt.Key.Key_Escape)

    assert visible_tag_prompts(viewer) == []
    assert stack.currentWidget() is viewer


def test_on_the_windows_launch_screen_esc_quits_the_app(qtbot):
    window = Window(player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)

    qtbot.keyClick(window.findChild(QStackedWidget).currentWidget(), Qt.Key.Key_Escape)

    assert not window.isVisible()


def test_on_the_windows_launch_screen_esc_in_a_dropped_folders_slideshow_shows_that_folders_grid(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    drag_and_drop_onto(stack.currentWidget(), tmp_path)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.folder == tmp_path
    assert shown.currentIndex().data(Qt.ItemDataRole.DisplayRole) == "a.jpg"


def test_in_the_windows_grid_enter_on_a_file_starts_that_folders_slideshow_at_that_file(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    make_image(tmp_path / "c.jpg", "green")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == tmp_path / "b.jpg"


def test_in_the_windows_grid_enter_on_a_folder_opens_that_folders_grid_with_the_cursor_on_its_first_entry(qtbot, tmp_path):
    (tmp_path / "day1").mkdir()
    make_image(tmp_path / "day1" / "x.jpg", "red")
    make_image(tmp_path / "day1" / "y.jpg", "blue")
    make_image(tmp_path / "a.jpg", "green")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Left)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(TILE_ROLE).path == tmp_path / "day1" / "x.jpg"


def test_in_the_windows_grid_backspace_opens_the_parent_folders_grid_with_the_cursor_on_the_folder_just_left(qtbot, tmp_path):
    (tmp_path / "day1").mkdir()
    make_image(tmp_path / "day1" / "x.jpg", "red")
    make_image(tmp_path / "a.jpg", "green")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Left)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Backspace)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(TILE_ROLE).path == tmp_path / "day1"


def test_in_the_windows_grid_of_a_drives_mount_point_backspace_stays_on_that_grid(qtbot, tmp_path):
    drive = tmp_path / "drive"
    drive.mkdir()
    make_image(drive / "a.jpg", "red")
    window = Window(drive, player_options=SILENT, is_mount_point=lambda path: path == drive,
        ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Backspace)

    shown = stack.currentWidget()
    assert isinstance(shown, Grid)
    assert shown.currentIndex().data(TILE_ROLE).path == drive / "a.jpg"


def test_in_the_windows_grid_esc_quits_the_app(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert not window.isVisible()


def test_in_the_windows_grid_f_toggles_fullscreen(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    was_fullscreen = window.isFullScreen()

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_F)

    assert window.isFullScreen() is not was_fullscreen


def test_in_the_windows_grid_f_twice_leaves_fullscreen_again(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    was_fullscreen = window.isFullScreen()

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_F)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_F)

    assert window.isFullScreen() is was_fullscreen


def test_dropping_a_folder_onto_the_windows_grid_starts_that_folders_slideshow(qtbot, tmp_path):
    viewed, dropped = make_folders(tmp_path, "viewed", "dropped")
    make_image(viewed / "a.jpg", "red")
    make_image(dropped / "x.jpg", "green")
    make_image(dropped / "y.jpg", "blue")
    window = Window(viewed, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    drag_and_drop_onto(stack.currentWidget().viewport(), dropped)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == dropped / "x.jpg"


def test_dropping_a_file_onto_the_windows_grid_starts_its_folders_slideshow_at_that_file(qtbot, tmp_path):
    viewed, dropped = make_folders(tmp_path, "viewed", "dropped")
    make_image(viewed / "a.jpg", "red")
    make_image(dropped / "x.jpg", "green")
    make_image(dropped / "y.jpg", "blue")
    window = Window(viewed, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    drag_and_drop_onto(stack.currentWidget().viewport(), dropped / "y.jpg")

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == dropped / "y.jpg"


def test_after_going_back_and_forth_between_grids_and_the_viewer_many_times_the_window_holds_only_the_grid_shown(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)

    for _ in range(5):
        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    assert window.findChildren(Grid) == [stack.currentWidget()]


def shown_status_bar_texts(window):
    return [label.text() for bar in window.findChildren(StatusBar) for label in bar.findChildren(QLabel) if label.isVisible()]


def window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach family")
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    return window, stack


def test_moving_the_windows_grid_cursor_onto_a_tagged_item_shows_its_own_tags_space_separated_in_the_status_bar(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    assert "beach family" in shown_status_bar_texts(window)


def test_moving_the_windows_grid_cursor_onto_an_untagged_item_shows_no_tags_in_the_status_bar(qtbot, tmp_path):
    window, stack = window_showing_the_grid_of_a_folder_whose_second_item_is_tagged_beach_family(qtbot, tmp_path)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Right)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Left)

    shown = shown_status_bar_texts(window)
    assert "beach family" not in shown
    assert "" not in shown


def test_the_library_status_of_a_read_only_drive_stays_visible_in_the_status_bar_while_the_windows_grid_is_shown(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
        qtbot.addWidget(window)
        show_exposed(qtbot, window)
        stack = window.findChild(QStackedWidget)

        qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert isinstance(stack.currentWidget(), Grid)
    assert READ_ONLY_STATUS_TEXT in shown_status_bar_texts(window)


def test_a_backup_failure_shown_in_the_windows_viewer_stays_visible_in_the_status_bar_after_esc_shows_the_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    (backup_root / Library.open(drive).drive_id / "drive.json").mkdir(parents=True)
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False, backup_root=backup_root)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    assert isinstance(stack.currentWidget(), Grid)
    assert BACKUP_FAILED_TEXT.format(os.strerror(errno.EISDIR)) in shown_status_bar_texts(window)


def test_going_from_the_windows_viewer_to_the_grid_and_back_on_the_same_drive_makes_no_new_backup(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    ticks = iter(datetime(2026, 10, 10, 12, 0, second, tzinfo=timezone.utc) for second in range(60))
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False, backup_root=backup_root, backup_clock=lambda: next(ticks))
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    enter_in_tag_prompt(qtbot, stack.currentWidget(), "sunset")
    backups_before = sorted((backup_root / Library.open(drive).drive_id).glob("tags-*.db"))

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Return)

    assert isinstance(stack.currentWidget(), Viewer)
    assert sorted((backup_root / Library.open(drive).drive_id).glob("tags-*.db")) == backups_before
