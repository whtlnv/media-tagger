import errno
from pathlib import Path

from PySide6.QtCore import QMimeData, QPointF, Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QFileDialog, QLabel

from mediatagger.test_video import make_clip
from mediatagger.test_viewer import (
    centre_colour, make_folder_with_no_media, make_image, shown_labels, shown_launch_viewer, shown_texts, shown_viewer_on,
    SILENT, shows_unsupported_placeholder, shows_video_surface, wait_until_loaded,
)
from mediatagger import viewer as viewer_module
from mediatagger.viewer import LIBRARY_TEXT, NO_LIBRARY_TEXT, Viewer


def make_folders(parent, *names):
    folders = [parent / name for name in names]
    for folder in folders:
        folder.mkdir()
    return folders


def modal_opened_by_key(qtbot, viewer, key):
    modals = []

    def close_whatever_is_open():
        modal = QApplication.activeModalWidget()
        modals.append(modal)
        if modal is not None:
            modal.reject()

    QTimer.singleShot(200, close_whatever_is_open)
    qtbot.keyClick(viewer, key)
    qtbot.waitUntil(lambda: len(modals) == 1)
    return modals[0]


def finish_o_dialog_pointed_at(qtbot, viewer, folder, finish):
    def point_and_finish():
        dialog = QApplication.activeModalWidget()
        dialog.setDirectory(str(folder))
        getattr(dialog, finish)()

    QTimer.singleShot(200, point_and_finish)
    qtbot.keyClick(viewer, Qt.Key.Key_O)


def dragged_local_path(path):
    dragged = QMimeData()
    dragged.setUrls([QUrl.fromLocalFile(str(path))])
    return dragged


def drag_enter_over(viewer, dragged):
    drag_enter = QDragEnterEvent(
        QPointF(viewer.rect().center()), Qt.DropAction.CopyAction, dragged, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(viewer, drag_enter)
    return drag_enter


def drop_onto(viewer, dragged):
    drop = QDropEvent(
        QPointF(viewer.rect().center()), Qt.DropAction.CopyAction, dragged, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(viewer, drop)


def drag_and_drop_onto(viewer, path):
    dragged = dragged_local_path(path)
    drag_enter_over(viewer, dragged)
    drop_onto(viewer, dragged)


def viewer_past_its_first_item_beside_a_green_then_yellow_folder(qtbot, tmp_path):
    viewed, dropped = make_folders(tmp_path, "viewed", "dropped")
    make_image(viewed / "IMG_1.png", "red")
    make_image(viewed / "IMG_2.png", "blue")
    make_image(dropped / "IMG_1.png", "green")
    make_image(dropped / "IMG_2.png", "yellow")
    viewer = shown_viewer_on(qtbot, viewed)
    qtbot.keyClick(viewer, Qt.Key.Key_Right)
    return viewer, dropped


def test_the_launch_screen_text_shows_the_o_key_without_backticks(qtbot):
    viewer = shown_launch_viewer(qtbot)

    assert shown_texts(viewer) == ["Drop a folder or file here, or press o to open"]


def status_bar_texts(viewer):
    return [label.text() for label in viewer.status_bar.findChildren(QLabel) if not label.isHidden()]


def make_tag_library_drive(drive):
    (drive / ".mediatagger").mkdir(parents=True)
    (drive / ".mediatagger" / "tags.db").touch()
    return drive


def test_the_launch_screen_status_bar_says_no_library_is_open(qtbot):
    viewer = shown_launch_viewer(qtbot)

    assert status_bar_texts(viewer) == [NO_LIBRARY_TEXT]


def test_opening_a_folder_two_levels_below_a_drive_with_a_tag_library_names_that_drive_in_the_status_bar(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    folder = drive / "Photos" / "2024"
    folder.mkdir(parents=True)
    make_image(folder / "IMG_1.png", "red")

    viewer = Viewer(folder, player_options=SILENT, is_mount_point=lambda path: path == drive)
    qtbot.addWidget(viewer)

    assert status_bar_texts(viewer) == [LIBRARY_TEXT.format("MEDIATAGGER")]


def test_opening_a_folder_that_is_itself_a_drives_mount_point_with_a_tag_library_names_that_folder_in_the_status_bar(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    make_image(drive / "IMG_1.png", "red")

    viewer = Viewer(drive, player_options=SILENT, is_mount_point=lambda path: path == drive)
    qtbot.addWidget(viewer)

    assert status_bar_texts(viewer) == [LIBRARY_TEXT.format("MEDIATAGGER")]


def test_opening_a_file_on_a_drive_names_the_same_library_in_the_status_bar_as_opening_its_folder(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    folder = drive / "Photos" / "2024"
    folder.mkdir(parents=True)
    make_image(folder / "IMG_1.png", "red")
    make_image(folder / "IMG_2.png", "blue")
    folder_viewer = Viewer(folder, player_options=SILENT, is_mount_point=lambda path: path == drive)
    qtbot.addWidget(folder_viewer)

    file_viewer = Viewer(folder / "IMG_2.png", player_options=SILENT, is_mount_point=lambda path: path == drive)
    qtbot.addWidget(file_viewer)

    assert status_bar_texts(file_viewer) == status_bar_texts(folder_viewer)


def test_dropping_a_folder_from_a_different_drive_while_viewing_switches_the_status_bar_to_that_drives_library(qtbot, tmp_path):
    first_drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    second_drive = make_tag_library_drive(tmp_path / "BACKUP")
    [viewed] = make_folders(first_drive, "Photos")
    [dropped] = make_folders(second_drive, "Videos")
    make_image(viewed / "IMG_1.png", "red")
    make_image(dropped / "IMG_1.png", "green")
    viewer = Viewer(viewed, player_options=SILENT, is_mount_point=lambda path: path in (first_drive, second_drive))
    qtbot.addWidget(viewer)

    drag_and_drop_onto(viewer, dropped)

    assert status_bar_texts(viewer) == [LIBRARY_TEXT.format("BACKUP")]


def test_opening_a_folder_on_the_system_disk_never_asks_to_create_a_library_and_the_status_bar_says_no_library_viewing_only(qtbot, tmp_path):
    folder = tmp_path / "Photos"
    folder.mkdir()
    make_image(folder / "IMG_1.png", "red")
    asked = []

    viewer = Viewer(
        folder, player_options=SILENT, is_mount_point=lambda path: path == Path("/"), ask_to_create_library=asked.append,
    )
    qtbot.addWidget(viewer)

    assert asked == []
    assert status_bar_texts(viewer) == [viewer_module.NO_LIBRARY_VIEWING_ONLY_TEXT]


def test_a_viewer_opened_on_a_folder_shows_its_first_item_and_not_the_launch_text(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_viewer_on(qtbot, tmp_path)

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("red")


def test_pressing_o_on_the_launch_screen_opens_a_folder_picker(qtbot):
    viewer = shown_launch_viewer(qtbot)

    picker = modal_opened_by_key(qtbot, viewer, Qt.Key.Key_O)

    assert isinstance(picker, QFileDialog)
    assert picker.fileMode() == QFileDialog.FileMode.Directory


def test_pressing_a_key_other_than_o_on_the_launch_screen_opens_no_folder_picker_and_keeps_the_launch_text(qtbot):
    viewer = shown_launch_viewer(qtbot)
    launch_text = shown_texts(viewer)

    modal = modal_opened_by_key(qtbot, viewer, Qt.Key.Key_X)

    assert modal is None
    assert shown_texts(viewer) == launch_text


def test_choosing_a_folder_in_the_o_picker_starts_that_folders_slideshow_at_its_first_item(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_launch_viewer(qtbot, folder_picker=lambda: tmp_path)

    qtbot.keyClick(viewer, Qt.Key.Key_O)

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("red")


def test_cancelling_the_o_picker_leaves_the_launch_text_showing(qtbot):
    viewer = shown_launch_viewer(qtbot)
    launch_text = shown_texts(viewer)

    modal_opened_by_key(qtbot, viewer, Qt.Key.Key_O)

    assert shown_texts(viewer) == launch_text


def test_accepting_the_viewers_own_o_dialog_pointed_at_a_folder_starts_that_folders_slideshow_at_its_first_item(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_launch_viewer(qtbot)

    finish_o_dialog_pointed_at(qtbot, viewer, tmp_path, "accept")

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("red")


def test_rejecting_the_viewers_own_o_dialog_pointed_at_a_folder_leaves_the_launch_text_showing(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    viewer = shown_launch_viewer(qtbot)
    launch_text = shown_texts(viewer)

    finish_o_dialog_pointed_at(qtbot, viewer, tmp_path, "reject")

    assert shown_texts(viewer) == launch_text


def test_choosing_a_folder_with_no_media_in_the_o_picker_says_so_like_opening_that_folder_does(qtbot, tmp_path):
    folder = make_folder_with_no_media(tmp_path / "Holidays")
    viewer = shown_launch_viewer(qtbot, folder_picker=lambda: folder)

    qtbot.keyClick(viewer, Qt.Key.Key_O)

    assert shown_texts(viewer) == shown_texts(shown_viewer_on(qtbot, folder))


def test_dragging_a_folder_from_the_file_manager_over_the_viewer_is_accepted_as_a_drop(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    viewer = shown_launch_viewer(qtbot)
    dragged = dragged_local_path(tmp_path)

    drag_enter = drag_enter_over(viewer, dragged)

    assert drag_enter.isAccepted()


def test_dragging_plain_text_over_the_viewer_is_refused(qtbot):
    viewer = shown_launch_viewer(qtbot)
    dragged = QMimeData()
    dragged.setText("just some words")

    drag_enter = drag_enter_over(viewer, dragged)

    assert not drag_enter.isAccepted()


def test_dragging_a_web_link_over_the_viewer_is_refused(qtbot):
    viewer = shown_launch_viewer(qtbot)
    dragged = QMimeData()
    dragged.setUrls([QUrl("https://example.com/photo.jpg")])

    drag_enter = drag_enter_over(viewer, dragged)

    assert not drag_enter.isAccepted()


def test_dropping_a_folder_onto_the_launch_screen_starts_that_folders_slideshow_at_its_first_item(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_launch_viewer(qtbot)

    drag_and_drop_onto(viewer, tmp_path)

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("red")


def test_dropping_a_file_onto_the_launch_screen_starts_its_folders_slideshow_at_that_file(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_launch_viewer(qtbot)

    drag_and_drop_onto(viewer, tmp_path / "IMG_2.png")

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("blue")


def test_dropping_a_folder_whose_first_item_cannot_be_decoded_onto_the_launch_screen_shows_the_unsupported_placeholder_not_the_launch_text(qtbot, tmp_path):
    (tmp_path / "IMG_1.png").write_bytes(b"not really a png")
    make_image(tmp_path / "IMG_2.png", "red")
    viewer = shown_launch_viewer(qtbot)
    launch_text = shown_texts(viewer)

    drag_and_drop_onto(viewer, tmp_path)

    assert shown_texts(viewer) != launch_text
    assert shows_unsupported_placeholder(viewer)


def test_dropping_a_folder_with_no_media_while_an_image_is_showing_says_so_and_no_longer_paints_that_image(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    empty = make_folder_with_no_media(tmp_path / "Holidays")
    viewer = shown_viewer_on(qtbot, tmp_path)

    drag_and_drop_onto(viewer, empty)

    assert shown_texts(viewer) == shown_texts(shown_viewer_on(qtbot, empty))
    frame = viewer.grab().toImage()
    assert frame.pixelColor(10, frame.height() // 2) == QColor("black")


def test_the_no_media_text_shown_after_dropping_an_empty_folder_onto_the_launch_screen_is_centred_in_the_window(qtbot, tmp_path):
    empty = make_folder_with_no_media(tmp_path / "Holidays")
    viewer = shown_launch_viewer(qtbot)
    viewer.resize(600, 500)
    qtbot.waitUntil(lambda: viewer.width() == 600)

    drag_and_drop_onto(viewer, empty)

    frame = viewer.grab().toImage()
    lit = [(x, y) for x in range(frame.width()) for y in range(frame.height()) if frame.pixelColor(x, y).lightness() > 200]
    xs, ys = [x for x, _ in lit], [y for _, y in lit]
    text_centre_x, text_centre_y = (min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2
    assert abs(text_centre_x - frame.width() // 2) <= 4
    assert abs(text_centre_y - frame.height() // 2) <= 4


def test_a_viewer_opened_on_a_folder_that_does_not_exist_shows_a_centred_cant_open_message_naming_it(qtbot, tmp_path):
    missing = tmp_path / "Holidays"

    viewer = shown_viewer_on(qtbot, missing)

    assert shown_texts(viewer) == ["Can't open Holidays"]
    message = shown_labels(viewer)[0]
    assert abs(message.geometry().center().x() - viewer.rect().center().x()) <= 1
    assert abs(message.geometry().center().y() - viewer.rect().center().y()) <= 1


def test_a_viewer_opened_on_a_file_in_a_missing_folder_shows_a_cant_open_message_naming_the_file(qtbot, tmp_path):
    missing = tmp_path / "no_such_folder" / "does_not_exist.jpg"

    viewer = shown_viewer_on(qtbot, missing)

    assert shown_texts(viewer) == ["Can't open does_not_exist.jpg"]


def test_a_viewer_opened_on_a_folder_it_is_not_allowed_to_read_shows_a_cant_open_message_naming_it(qtbot, tmp_path):
    locked = tmp_path / "Private"
    locked.mkdir()
    locked.chmod(0o000)
    try:
        viewer = shown_viewer_on(qtbot, locked)
    finally:
        locked.chmod(0o755)

    assert shown_texts(viewer) == ["Can't open Private"]


def test_a_viewer_opened_on_a_readable_image_in_a_folder_it_is_not_allowed_to_list_shows_a_cant_open_message_naming_the_file(qtbot, tmp_path):
    unlistable = tmp_path / "Private"
    unlistable.mkdir()
    image = make_image(unlistable / "IMG_1.png", "red")
    unlistable.chmod(0o111)
    try:
        viewer = shown_viewer_on(qtbot, image)
    finally:
        unlistable.chmod(0o755)

    assert shown_texts(viewer) == ["Can't open IMG_1.png"]


def test_dropping_a_folder_while_viewing_another_folder_replaces_the_slideshow_with_the_dropped_folders_at_its_first_item(qtbot, tmp_path):
    viewer, dropped = viewer_past_its_first_item_beside_a_green_then_yellow_folder(qtbot, tmp_path)

    drag_and_drop_onto(viewer, dropped)

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("green")


def test_dropping_a_file_while_viewing_another_folder_replaces_the_slideshow_with_that_files_folder_at_that_file(qtbot, tmp_path):
    viewer, dropped = viewer_past_its_first_item_beside_a_green_then_yellow_folder(qtbot, tmp_path)

    drag_and_drop_onto(viewer, dropped / "IMG_2.png")

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("yellow")


def test_dropping_a_folder_while_the_i_overlay_is_shown_shows_the_dropped_folders_first_filename_and_position(qtbot, tmp_path):
    viewed, dropped = make_folders(tmp_path, "viewed", "dropped")
    make_image(viewed / "IMG_1.png", "red")
    make_image(viewed / "IMG_2.png", "blue")
    for n in (1, 2, 3):
        make_image(dropped / f"PHOTO_{n}.png", "green")
    viewer = shown_viewer_on(qtbot, viewed)
    qtbot.keyClick(viewer, Qt.Key.Key_Right)
    qtbot.keyClick(viewer, Qt.Key.Key_I)

    drag_and_drop_onto(viewer, dropped)

    assert len(shown_texts(viewer)) == 1
    text = shown_texts(viewer)[0]
    assert "PHOTO_1.png" in text and "1 / 3" in text


def test_dropping_a_folder_while_a_video_is_playing_stops_that_videos_playback_and_sound(qtbot, tmp_path):
    viewed, dropped = make_folders(tmp_path, "viewed", "dropped")
    clip = make_clip(viewed / "IMG_1.mp4")
    make_image(dropped / "IMG_1.png", "green")
    viewer = shown_viewer_on(qtbot, viewed)
    wait_until_loaded(viewer.video_player.engine, clip)

    drag_and_drop_onto(viewer, dropped)

    assert viewer.video_player.engine.path is None


def test_dropping_a_folder_with_no_media_while_a_video_is_showing_hides_the_video_surface_and_says_so(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    empty = make_folder_with_no_media(tmp_path / "Holidays")
    viewer = shown_viewer_on(qtbot, tmp_path)
    wait_until_loaded(viewer.video_player.engine, clip)

    drag_and_drop_onto(viewer, empty)

    assert shown_texts(viewer) == shown_texts(shown_viewer_on(qtbot, empty))
    assert not shows_video_surface(viewer)


def test_dropping_a_folder_with_no_media_while_the_info_overlay_is_shown_hides_the_overlay(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    empty = make_folder_with_no_media(tmp_path / "Holidays")
    viewer = shown_viewer_on(qtbot, tmp_path)
    qtbot.keyClick(viewer, Qt.Key.Key_I)

    drag_and_drop_onto(viewer, empty)

    assert shown_texts(viewer) == shown_texts(shown_viewer_on(qtbot, empty))


def test_dropping_a_folder_that_does_not_exist_while_a_video_is_showing_stops_it_hides_its_surface_and_says_it_cant_open_it(qtbot, tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4")
    missing = tmp_path / "Holidays"
    viewer = shown_viewer_on(qtbot, tmp_path)
    wait_until_loaded(viewer.video_player.engine, clip)

    drag_and_drop_onto(viewer, missing)

    assert viewer.video_player.engine.path is None
    assert not shows_video_surface(viewer)
    assert shown_texts(viewer) == shown_texts(shown_viewer_on(qtbot, missing))


def test_dropping_a_folder_that_does_not_exist_while_the_info_overlay_is_shown_hides_the_overlay(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    missing = tmp_path / "Holidays"
    viewer = shown_viewer_on(qtbot, tmp_path)
    qtbot.keyClick(viewer, Qt.Key.Key_I)

    drag_and_drop_onto(viewer, missing)

    assert shown_texts(viewer) == shown_texts(shown_viewer_on(qtbot, missing))


def test_dropping_a_readable_folder_after_cant_open_is_shown_starts_that_folders_slideshow_at_its_first_item(qtbot, tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    viewer = shown_viewer_on(qtbot, tmp_path / "Holidays")

    drag_and_drop_onto(viewer, tmp_path)

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("red")


def test_choosing_a_readable_folder_in_the_o_dialog_after_cant_open_is_shown_starts_that_folders_slideshow(qtbot, tmp_path):
    trip, holidays = make_folders(tmp_path, "Trip", "Holidays")
    make_image(trip / "IMG_1.png", "blue")
    make_image(holidays / "IMG_1.png", "red")
    viewer = shown_viewer_on(qtbot, trip)
    drag_and_drop_onto(viewer, tmp_path / "Missing")

    finish_o_dialog_pointed_at(qtbot, viewer, holidays, "accept")

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("red")


def test_a_viewer_opened_on_a_folder_whose_listing_fails_with_an_io_error_says_it_cant_open_it_and_a_dropped_readable_folder_still_starts(qtbot, tmp_path, monkeypatch):
    unplugged, readable = make_folders(tmp_path, "USB", "Trip")
    make_image(unplugged / "IMG_1.png", "blue")
    make_image(readable / "IMG_1.png", "red")
    real_iterdir = Path.iterdir

    def iterdir_failing_on_the_unplugged_drive(path):
        if path == unplugged:
            raise OSError(errno.EIO, "Input/output error")
        return real_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", iterdir_failing_on_the_unplugged_drive)
    viewer = shown_viewer_on(qtbot, unplugged)

    assert shown_texts(viewer) == shown_texts(shown_viewer_on(qtbot, tmp_path / "Missing" / "USB"))
    drag_and_drop_onto(viewer, readable)
    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("red")


def test_dropping_a_folder_whose_listing_fails_with_an_io_error_while_an_image_is_showing_no_longer_paints_it_and_o_opens_the_folder_picker(qtbot, tmp_path, monkeypatch):
    viewed, unplugged = make_folders(tmp_path, "Trip", "USB")
    make_image(viewed / "IMG_1.png", "red")
    make_image(unplugged / "IMG_1.png", "blue")
    real_iterdir = Path.iterdir

    def iterdir_failing_on_the_unplugged_drive(path):
        if path == unplugged:
            raise OSError(errno.EIO, "Input/output error")
        return real_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", iterdir_failing_on_the_unplugged_drive)
    viewer = shown_viewer_on(qtbot, viewed)

    drag_and_drop_onto(viewer, unplugged)

    frame = viewer.grab().toImage()
    assert frame.pixelColor(10, frame.height() // 2) == QColor("black")
    assert isinstance(modal_opened_by_key(qtbot, viewer, Qt.Key.Key_O), QFileDialog)
