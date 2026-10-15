from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QStackedWidget

from mediatagger.grid import TAG_BADGE, TILE_ROLE, Grid
from mediatagger.library import Library
from mediatagger.test_grid import drag_move_over, painted_texts
from mediatagger.test_thumbnail_cache import solid_thumbnail
from mediatagger.test_video import make_clip
from mediatagger.test_viewer import SILENT, make_image, make_surface_ready, show_exposed, shown_texts, wait_until_loaded
from mediatagger.test_viewer_library import (
    drive_with_a_tag_library_holding_one_image, made_read_only, make_tag_library_drive, visible_tag_prompt_texts, visible_tag_prompts,
)
from mediatagger.test_viewer_open import drag_and_drop_onto, drag_enter_over, dragged_local_path, drop_onto, make_folders
from mediatagger.thumbnail_cache import ThumbnailCache, cache_file
from mediatagger.viewer import READ_ONLY_BANNER_TEXT, Viewer
from mediatagger.window import Window


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


def test_dragging_a_folder_over_the_windows_grid_viewport_and_dropping_it_shows_that_folders_slideshow_from_its_first_item(qtbot, tmp_path):
    viewed, dropped = make_folders(tmp_path, "viewed", "dropped")
    make_image(viewed / "a.jpg", "red")
    make_image(dropped / "y.jpg", "blue")
    make_image(dropped / "x.jpg", "green")
    window = Window(viewed, player_options=SILENT)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    drag_move_and_drop_onto(stack.currentWidget().viewport(), dropped)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == dropped / "x.jpg"


def test_dragging_a_folder_of_another_drive_over_the_windows_grid_viewport_and_dropping_it_then_esc_shows_that_folders_grid_with_the_new_drives_tag_badges(qtbot, tmp_path):
    first_drive, viewed, second_drive, dropped = a_second_drive_with_a_folder_holding_one_blue_image(tmp_path)
    Library.open(second_drive).enter(dropped / "x.png", "beach family")
    window = Window(viewed, player_options=SILENT, is_mount_point=lambda path: path in (first_drive, second_drive), ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    drag_move_and_drop_onto(stack.currentWidget().viewport(), dropped)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    grid = stack.currentWidget()
    assert isinstance(grid, Grid)
    assert grid.folder == dropped
    assert f"{TAG_BADGE}2" in painted_texts(grid, 0)


def test_dragging_a_folder_of_another_drive_over_the_video_surface_of_the_windows_viewer_while_a_video_plays_and_dropping_it_shows_that_folders_slideshow_from_its_first_item(qtbot, tmp_path):
    first_drive, viewed, second_drive, dropped = a_second_drive_with_a_folder_holding_one_blue_image(tmp_path)
    clip = make_clip(viewed / "a.mp4")
    make_image(dropped / "w.png", "green")
    window = Window(clip, player_options=SILENT, is_mount_point=lambda path: path in (first_drive, second_drive), ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    viewer = stack.currentWidget()
    make_surface_ready(viewer)
    wait_until_loaded(viewer.video_player.engine, clip)

    drag_move_and_drop_onto(viewer.surface, dropped)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == dropped / "w.png"


def test_pressing_o_in_the_windows_grid_opens_the_folder_picker_and_choosing_a_folder_shows_its_slideshow_from_its_first_item(qtbot, tmp_path):
    viewed, chosen = make_folders(tmp_path, "viewed", "chosen")
    make_image(viewed / "a.jpg", "red")
    make_image(chosen / "y.jpg", "blue")
    make_image(chosen / "x.jpg", "green")
    window = Window(viewed, player_options=SILENT, folder_picker=lambda: chosen)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_O)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == chosen / "x.jpg"


def test_pressing_o_in_the_windows_viewer_on_an_image_opens_the_folder_picker_and_choosing_a_folder_shows_its_slideshow_from_its_first_item(qtbot, tmp_path):
    viewed, chosen = make_folders(tmp_path, "viewed", "chosen")
    make_image(viewed / "a.jpg", "red")
    make_image(chosen / "y.jpg", "blue")
    make_image(chosen / "x.jpg", "green")
    window = Window(viewed, player_options=SILENT, folder_picker=lambda: chosen)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_O)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == chosen / "x.jpg"


def test_pressing_o_in_the_windows_viewer_while_a_video_plays_opens_the_folder_picker_and_choosing_a_folder_shows_its_slideshow_from_its_first_item(qtbot, tmp_path):
    viewed, chosen = make_folders(tmp_path, "viewed", "chosen")
    clip = make_clip(viewed / "a.mp4")
    make_image(chosen / "y.jpg", "blue")
    make_image(chosen / "x.jpg", "green")
    window = Window(viewed, player_options=SILENT, folder_picker=lambda: chosen)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    viewer = stack.currentWidget()
    make_surface_ready(viewer)
    wait_until_loaded(viewer.video_player.engine, clip)

    qtbot.keyClick(QApplication.focusWidget() or viewer, Qt.Key.Key_O)

    shown = stack.currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow.current == chosen / "x.jpg"


def test_pressing_o_in_the_windows_viewer_while_a_video_plays_and_choosing_a_folder_of_images_leaves_the_player_stopped(qtbot, tmp_path):
    viewed, chosen = make_folders(tmp_path, "viewed", "chosen")
    clip = make_clip(viewed / "a.mp4")
    make_image(chosen / "x.jpg", "green")
    window = Window(viewed, player_options=SILENT, folder_picker=lambda: chosen)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()
    make_surface_ready(viewer)
    wait_until_loaded(viewer.video_player.engine, clip)

    qtbot.keyClick(QApplication.focusWidget() or viewer, Qt.Key.Key_O)

    qtbot.waitUntil(lambda: viewer.video_player.engine.path is None, timeout=3000)


def test_pressing_o_in_the_windows_viewer_and_cancelling_the_folder_picker_leaves_the_same_item_shown(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT, folder_picker=lambda: None)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    viewer = stack.currentWidget()
    qtbot.keyClick(viewer, Qt.Key.Key_Right)

    qtbot.keyClick(viewer, Qt.Key.Key_O)

    assert stack.currentWidget() is viewer
    assert viewer.slideshow.current == tmp_path / "b.jpg"


def test_pressing_o_in_the_windows_grid_and_cancelling_the_folder_picker_leaves_the_same_grid_shown_with_its_cursor_unchanged(qtbot, tmp_path):
    make_image(tmp_path / "a.jpg", "red")
    make_image(tmp_path / "b.jpg", "blue")
    window = Window(tmp_path, player_options=SILENT, folder_picker=lambda: None)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    grid = stack.currentWidget()
    qtbot.keyClick(grid, Qt.Key.Key_Right)

    qtbot.keyClick(grid, Qt.Key.Key_O)

    assert stack.currentWidget() is grid
    assert grid.currentIndex().data(TILE_ROLE).path == tmp_path / "b.jpg"


def test_pressing_o_while_the_windows_grid_tag_prompt_has_focus_types_an_o_into_the_prompt_and_opens_no_folder_picker(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    picked = []
    window = Window(folder, player_options=SILENT, folder_picker=lambda: picked.append(True), is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_T)
    [prompt] = visible_tag_prompts(window)

    qtbot.keyClick(prompt, Qt.Key.Key_O)

    assert visible_tag_prompt_texts(window) == ["o"]
    assert picked == []


def drag_move_and_drop_onto(widget, path):
    dragged = dragged_local_path(path)
    drag_enter_over(widget, dragged)
    if drag_move_over(widget, dragged).isAccepted():  # the platform drops only where the last move was accepted
        drop_onto(widget, dragged)


def a_second_drive_with_a_folder_holding_one_blue_image(tmp_path):
    first_drive, viewed = drive_with_a_tag_library_holding_one_image(tmp_path)
    second_drive = make_tag_library_drive(tmp_path / "ELSEWHERE")
    [chosen] = make_folders(second_drive, "Videos")
    make_image(chosen / "x.png", "blue")
    return first_drive, viewed, second_drive, chosen


def test_choosing_a_folder_of_another_drive_with_o_from_the_windows_grid_then_esc_shows_that_folders_grid_with_the_new_drives_tag_badges(qtbot, tmp_path):
    first_drive, viewed, second_drive, chosen = a_second_drive_with_a_folder_holding_one_blue_image(tmp_path)
    Library.open(second_drive).enter(chosen / "x.png", "beach family")
    window = Window(viewed, player_options=SILENT, folder_picker=lambda: chosen, is_mount_point=lambda path: path in (first_drive, second_drive),
                    ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_O)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    grid = stack.currentWidget()
    assert isinstance(grid, Grid)
    assert grid.folder == chosen
    assert f"{TAG_BADGE}2" in painted_texts(grid, 0)


def test_choosing_a_folder_of_another_drive_with_o_from_the_windows_grid_then_esc_shows_thumbnails_from_the_new_drives_thumbnail_cache(qtbot, tmp_path):
    first_drive, viewed, second_drive, chosen = a_second_drive_with_a_folder_holding_one_blue_image(tmp_path)
    cached = cache_file(Library.open(second_drive).drive_id, Path.home())
    cached.parent.mkdir(parents=True)
    stat = (chosen / "x.png").stat()
    ThumbnailCache(cached, root=second_drive).store(chosen / "x.png", stat.st_size, stat.st_mtime, solid_thumbnail("red"))
    window = Window(viewed, player_options=SILENT, folder_picker=lambda: chosen, is_mount_point=lambda path: path in (first_drive, second_drive))
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)
    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_O)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    tile = stack.currentWidget().model().index(0, 0).data(TILE_ROLE)
    qtbot.waitUntil(lambda: tile.thumbnail is not None)
    color = tile.thumbnail.pixelColor(tile.thumbnail.width() // 2, tile.thumbnail.height() // 2)
    assert color.red() > 200 and color.blue() < 50  # the cached red, not the blue the file would generate


def test_choosing_a_folder_of_another_read_only_drive_with_o_from_the_windows_viewer_shows_the_read_only_banner(qtbot, tmp_path):
    first_drive, viewed, second_drive, chosen = a_second_drive_with_a_folder_holding_one_blue_image(tmp_path)
    window = Window(viewed, player_options=SILENT, folder_picker=lambda: chosen, is_mount_point=lambda path: path in (first_drive, second_drive),
                    ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    viewer = window.findChild(QStackedWidget).currentWidget()

    with made_read_only(second_drive):
        qtbot.keyClick(viewer, Qt.Key.Key_O)
        shown = shown_texts(viewer)

    assert viewer.slideshow.current == chosen / "x.png"
    assert READ_ONLY_BANNER_TEXT in shown
