import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel, QLineEdit

from mediatagger.library import Library
from mediatagger.test_video import make_clip, wait_until_playing
from mediatagger.test_viewer import centre_colour, make_image, make_surface_ready, shown_labels, shown_launch_viewer, shown_texts, shown_viewer_on, SILENT, shows_video_surface
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders
from mediatagger.viewer import (
    APP_PACKAGE, CORNER_MARGIN, CREATE_LIBRARY_QUESTION, DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT, LIBRARY_TEXT, NO_LIBRARY_TEXT, NO_LIBRARY_VIEWING_ONLY_TEXT,
    READ_ONLY_BANNER_TEXT, READ_ONLY_STATUS_TEXT, Viewer,
)


def status_bar_labels(viewer):
    return [label for label in viewer.status_bar.findChildren(QLabel) if not label.isHidden()]


def status_bar_texts(viewer):
    return [label.text() for label in status_bar_labels(viewer)]


def make_tag_library_drive(drive):
    (drive / ".mediatagger").mkdir(parents=True)
    (drive / ".mediatagger" / "tags.db").touch()
    return drive


def drive_without_a_tag_library_holding_one_image(tmp_path):
    drive = tmp_path / "MEDIATAGGER"
    folder = drive / "Photos"
    folder.mkdir(parents=True)
    make_image(folder / "IMG_1.png", "red")
    return drive, folder


def drive_with_a_tag_library_holding_one_image(tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    return drive, folder


def app_package_on(drive):
    return drive / "mediatagger" / "app" / "mediatagger"


def viewer_on_drives(qtbot, folder, drives, ask_to_create_library, app_location=APP_PACKAGE):
    viewer = Viewer(
        folder, player_options=SILENT, is_mount_point=lambda path: path in drives,
        ask_to_create_library=ask_to_create_library, app_location=app_location,
    )
    qtbot.addWidget(viewer)
    return viewer


def viewer_on_drive(qtbot, folder, drive, ask_to_create_library, app_location=APP_PACKAGE):
    return viewer_on_drives(qtbot, folder, (drive,), ask_to_create_library, app_location)


def shown_viewer_on_drives(qtbot, folder, drives, ask_to_create_library):
    viewer = viewer_on_drives(qtbot, folder, drives, ask_to_create_library)
    viewer.resize(400, 300)
    viewer.show()
    qtbot.waitExposed(viewer)
    return viewer


def shown_viewer_on_drive(qtbot, folder, drive, ask_to_create_library):
    return shown_viewer_on_drives(qtbot, folder, (drive,), ask_to_create_library)


def visible_tag_prompts(viewer):
    return [prompt for prompt in viewer.findChildren(QLineEdit) if prompt.isVisible()]


def visible_tag_prompt_texts(viewer):
    return [prompt.text() for prompt in visible_tag_prompts(viewer)]


def enter_in_tag_prompt(qtbot, viewer, text):
    qtbot.keyClick(viewer, Qt.Key.Key_T)
    [prompt] = visible_tag_prompts(viewer)
    qtbot.keyClicks(prompt, text)
    qtbot.keyClick(prompt, Qt.Key.Key_Return)


def decline_noting_the_question_in(asked):
    def decline(question):
        asked.append(question)
        return False
    return decline


@contextmanager
def made_read_only(drive):
    drive.chmod(0o555)
    try:
        yield
    finally:
        drive.chmod(0o755)


def test_the_launch_screen_status_bar_says_no_library_is_open(qtbot):
    viewer = shown_launch_viewer(qtbot)

    assert status_bar_texts(viewer) == [NO_LIBRARY_TEXT]


def test_opening_a_folder_two_levels_below_a_drive_with_a_tag_library_names_that_drive_in_the_status_bar(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    folder = drive / "Photos" / "2024"
    folder.mkdir(parents=True)
    make_image(folder / "IMG_1.png", "red")

    viewer = viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert status_bar_texts(viewer) == [LIBRARY_TEXT.format("MEDIATAGGER")]


def test_opening_a_folder_that_is_itself_a_drives_mount_point_with_a_tag_library_names_that_folder_in_the_status_bar(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    make_image(drive / "IMG_1.png", "red")

    viewer = viewer_on_drive(qtbot, drive, drive, lambda question: False)

    assert status_bar_texts(viewer) == [LIBRARY_TEXT.format("MEDIATAGGER")]


def test_opening_a_file_on_a_drive_names_the_same_library_in_the_status_bar_as_opening_its_folder(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    folder = drive / "Photos" / "2024"
    folder.mkdir(parents=True)
    make_image(folder / "IMG_1.png", "red")
    make_image(folder / "IMG_2.png", "blue")
    folder_viewer = viewer_on_drive(qtbot, folder, drive, lambda question: False)

    file_viewer = viewer_on_drive(qtbot, folder / "IMG_2.png", drive, lambda question: False)

    assert status_bar_texts(file_viewer) == status_bar_texts(folder_viewer)


def test_dropping_a_folder_from_a_different_drive_while_viewing_switches_the_status_bar_to_that_drives_library(qtbot, tmp_path):
    first_drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    second_drive = make_tag_library_drive(tmp_path / "BACKUP")
    [viewed] = make_folders(first_drive, "Photos")
    [dropped] = make_folders(second_drive, "Videos")
    make_image(viewed / "IMG_1.png", "red")
    make_image(dropped / "IMG_1.png", "green")
    viewer = viewer_on_drives(qtbot, viewed, (first_drive, second_drive), lambda question: False)

    drag_and_drop_onto(viewer, dropped)

    assert status_bar_texts(viewer) == [LIBRARY_TEXT.format("BACKUP")]


def test_opening_a_folder_on_the_system_disk_never_asks_to_create_a_library_and_the_status_bar_says_no_library_viewing_only(qtbot, tmp_path):
    folder = tmp_path / "Photos"
    folder.mkdir()
    make_image(folder / "IMG_1.png", "red")
    asked = []

    viewer = viewer_on_drive(qtbot, folder, Path("/"), asked.append)

    assert asked == []
    assert status_bar_texts(viewer) == [NO_LIBRARY_VIEWING_ONLY_TEXT]


def test_opening_a_folder_on_the_drive_the_app_runs_from_never_asks_to_create_a_library_writes_nothing_and_says_no_library_viewing_only(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    asked = []

    viewer = viewer_on_drive(qtbot, folder, drive, decline_noting_the_question_in(asked), app_package_on(drive))

    assert asked == []
    assert not (drive / ".mediatagger").exists()
    assert status_bar_texts(viewer) == [NO_LIBRARY_VIEWING_ONLY_TEXT]


def test_opening_a_folder_on_the_drive_the_app_runs_from_that_already_has_a_tag_library_does_not_open_it_and_says_no_library_viewing_only(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)

    viewer = viewer_on_drive(qtbot, folder, drive, lambda question: False, app_package_on(drive))

    assert status_bar_texts(viewer) == [NO_LIBRARY_VIEWING_ONLY_TEXT]


def test_opening_a_folder_on_a_drive_without_a_tag_library_asks_to_create_one_on_that_drive_before_writing_to_it(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    asked = []

    def decline_noting_whether_the_drive_was_written(question):
        asked.append((question, (drive / ".mediatagger").exists()))
        return False

    viewer_on_drive(qtbot, folder, drive, decline_noting_whether_the_drive_was_written)

    assert asked == [(CREATE_LIBRARY_QUESTION.format("MEDIATAGGER"), False)]


def test_opening_a_folder_on_a_drive_whose_mediatagger_folder_holds_no_tags_db_asks_to_create_a_tag_library(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    (drive / ".mediatagger").mkdir()
    asked = []

    viewer_on_drive(qtbot, folder, drive, decline_noting_the_question_in(asked))

    assert asked == [CREATE_LIBRARY_QUESTION.format("MEDIATAGGER")]


def test_opening_a_folder_on_a_drive_that_already_has_a_tag_library_does_not_ask_to_create_one(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    asked = []

    viewer_on_drive(qtbot, folder, drive, asked.append)

    assert asked == []


def test_accepting_to_create_a_tag_library_on_a_drive_creates_it_and_names_the_drive_as_the_open_library(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)

    viewer = viewer_on_drive(qtbot, folder, drive, lambda question: True)

    assert (drive / ".mediatagger" / "tags.db").is_file()
    assert status_bar_texts(viewer) == [LIBRARY_TEXT.format("MEDIATAGGER")]


def test_accepting_to_create_a_tag_library_on_a_drive_whose_mediatagger_folder_holds_no_tags_db_creates_it_there_and_names_the_drive(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    (drive / ".mediatagger").mkdir()

    viewer = viewer_on_drive(qtbot, folder, drive, lambda question: True)

    assert (drive / ".mediatagger" / "tags.db").is_file()
    assert status_bar_texts(viewer) == [LIBRARY_TEXT.format("MEDIATAGGER")]


def test_accepting_to_create_a_tag_library_on_a_drive_creates_a_real_library_whose_tags_db_reports_a_drive_id(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)

    viewer_on_drive(qtbot, folder, drive, lambda question: True)

    connection = sqlite3.connect(drive / ".mediatagger" / "tags.db")
    try:
        meta = dict(connection.execute("SELECT key, value FROM meta"))
    finally:
        connection.close()
    assert meta == {"drive_id": Library.open(drive).drive_id, "schema_version": str(Library.schema_version)}


def test_declining_to_create_a_tag_library_on_a_drive_leaves_the_drive_without_a_mediatagger_folder(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)

    viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert not (drive / ".mediatagger").exists()


def test_declining_to_create_a_tag_library_on_a_drive_still_shows_the_opened_folders_slideshow_at_its_first_item(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")

    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert shown_labels(viewer) == []
    assert centre_colour(viewer) == QColor("red")


def test_after_declining_to_create_a_tag_library_on_a_drive_the_status_bar_says_the_drive_has_no_tag_library_and_viewing_only(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)

    viewer = viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert status_bar_texts(viewer) == [DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT.format("MEDIATAGGER")]


def test_after_declining_to_create_a_tag_library_on_a_drive_opening_another_folder_on_that_drive_does_not_ask_again(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    [other] = make_folders(drive, "Videos")
    make_image(other / "IMG_1.png", "green")
    asked = []

    viewer = viewer_on_drive(qtbot, folder, drive, decline_noting_the_question_in(asked))
    drag_and_drop_onto(viewer, other)

    assert asked == [CREATE_LIBRARY_QUESTION.format("MEDIATAGGER")]


def test_opening_a_folder_that_does_not_exist_on_a_drive_without_a_tag_library_does_not_ask_to_create_one(qtbot, tmp_path):
    drive, _ = drive_without_a_tag_library_holding_one_image(tmp_path)
    asked = []

    viewer = shown_viewer_on_drive(qtbot, drive / "Holidays", drive, decline_noting_the_question_in(asked))

    assert asked == []
    assert shown_texts(viewer) == shown_texts(shown_viewer_on(qtbot, tmp_path / "Holidays"))


def test_opening_a_folder_on_a_read_only_drive_that_has_a_tag_library_shows_a_banner_saying_tags_cant_be_saved(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert shown_texts(viewer) == [READ_ONLY_BANNER_TEXT]


def test_opening_a_folder_on_a_read_only_drive_still_shows_its_slideshow_at_the_first_item(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
        shown = shown_texts(viewer)
        colour = centre_colour(viewer)

    assert shown == [READ_ONLY_BANNER_TEXT]
    assert colour == QColor("red")


def test_opening_a_folder_on_a_read_only_drive_that_has_a_tag_library_says_tags_cant_be_saved_in_the_status_bar(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert READ_ONLY_STATUS_TEXT in status_bar_texts(viewer)


def test_on_a_read_only_drive_with_a_tag_library_the_status_bar_texts_sit_side_by_side_inside_the_window_clear_of_its_left_and_bottom_edges(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    shown = status_bar_labels(viewer)
    left, right = sorted((QRect(label.mapTo(viewer, QPoint()), label.size()) for label in shown), key=lambda frame: frame.left())
    assert len(shown) == 2
    assert viewer.rect().contains(left) and viewer.rect().contains(right)
    assert left.left() >= CORNER_MARGIN
    assert max(left.bottom(), right.bottom()) <= viewer.rect().bottom() - CORNER_MARGIN
    assert left.right() < right.left()


def test_the_status_bar_text_is_shown_whole_with_room_for_its_full_height(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)

    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert viewer.library_label.height() >= viewer.library_label.sizeHint().height()
    assert viewer.library_label.width() == viewer.library_label.sizeHint().width()


def test_the_question_to_create_a_tag_library_is_asked_over_the_dropped_folders_first_image_not_a_placeholder(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    texts_shown_when_asked = []
    viewer = Viewer(
        player_options=SILENT, is_mount_point=lambda path: path == drive,
        ask_to_create_library=lambda question: texts_shown_when_asked.append(shown_texts(viewer)),
    )
    qtbot.addWidget(viewer)
    viewer.show()
    qtbot.waitExposed(viewer)

    drag_and_drop_onto(viewer, folder)

    assert texts_shown_when_asked == [[]]


def test_the_status_bar_text_stays_on_top_of_a_playing_video(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    [folder] = make_folders(drive, "Clips")
    make_clip(folder / "IMG_1.mp4")

    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.waitUntil(lambda: shows_video_surface(viewer))

    status_text_centre = viewer.library_label.mapTo(viewer, viewer.library_label.rect().center())
    assert viewer.childAt(status_text_centre) is viewer.library_label


def test_on_a_read_only_drive_with_a_tag_library_each_status_bar_text_is_styled_like_the_info_overlay(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    shown = status_bar_labels(viewer)
    assert len(shown) == 2
    assert [label.styleSheet() for label in shown] == [viewer.info.styleSheet()] * 2


def test_on_a_read_only_drive_with_a_tag_library_the_read_only_banner_is_styled_like_the_info_overlay(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    [banner] = shown_labels(viewer)
    assert banner.text() == READ_ONLY_BANNER_TEXT
    assert banner.styleSheet() == viewer.info.styleSheet()


def test_on_a_read_only_drive_with_a_tag_library_the_read_only_banner_sits_centred_horizontally_a_corner_margin_below_the_top_edge(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    viewer.resize(1600, 900)
    qtbot.waitUntil(lambda: viewer.width() == 1600)

    [banner] = shown_labels(viewer)
    frame = QRect(banner.mapTo(viewer, QPoint()), banner.size())
    assert frame.top() == CORNER_MARGIN
    assert abs(frame.center().x() - viewer.rect().center().x()) <= 1


def test_opening_a_folder_on_a_read_only_drive_without_a_tag_library_shows_the_read_only_banner_instead_of_asking_to_create_one(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    asked = []

    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, decline_noting_the_question_in(asked))
        shown = shown_texts(viewer)

    assert asked == []
    assert shown == [READ_ONLY_BANNER_TEXT]


def test_opening_a_folder_on_a_writable_drive_that_has_a_tag_library_shows_no_read_only_banner(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert READ_ONLY_BANNER_TEXT not in shown_texts(viewer)


def test_after_viewing_a_read_only_drive_dropping_a_folder_from_a_writable_drive_without_a_tag_library_and_declining_hides_the_read_only_banner_and_status(qtbot, tmp_path):
    read_only_drive, viewed = drive_with_a_tag_library_holding_one_image(tmp_path)
    [writable_drive] = make_folders(tmp_path, "BACKUP")
    [dropped] = make_folders(writable_drive, "Videos")
    make_image(dropped / "IMG_1.png", "green")
    with made_read_only(read_only_drive):
        viewer = shown_viewer_on_drives(qtbot, viewed, (read_only_drive, writable_drive), lambda question: False)

        drag_and_drop_onto(viewer, dropped)
        shown = shown_texts(viewer)
        status = status_bar_texts(viewer)

    assert READ_ONLY_BANNER_TEXT not in shown
    assert READ_ONLY_STATUS_TEXT not in status


def test_after_viewing_a_drive_with_a_tag_library_opening_a_folder_on_a_read_only_drive_without_one_says_tags_cant_be_saved_and_no_longer_names_the_previous_library(qtbot, tmp_path):
    viewed_drive = make_tag_library_drive(tmp_path / "BACKUP")
    [viewed] = make_folders(viewed_drive, "Videos")
    make_image(viewed / "IMG_1.png", "green")
    read_only_drive, dropped = drive_without_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(read_only_drive):
        viewer = viewer_on_drives(qtbot, viewed, (viewed_drive, read_only_drive), lambda question: False)

        drag_and_drop_onto(viewer, dropped)
        status = status_bar_texts(viewer)

    assert READ_ONLY_STATUS_TEXT in status
    assert LIBRARY_TEXT.format("BACKUP") not in status


def test_pressing_t_in_the_viewer_on_a_file_with_no_tags_opens_the_tag_prompt_showing_no_tags(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    Library.create(drive)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert visible_tag_prompt_texts(viewer) == [""]


def test_pressing_t_on_a_file_tagged_beach_family_shows_beach_family_as_text_beside_the_tag_prompts_empty_input(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    Library.create(drive).enter(folder / "IMG_1.png", "family beach")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert visible_tag_prompt_texts(viewer) == [""]
    assert "beach family" in shown_texts(viewer)


def test_typing_beach_family_in_the_tag_prompt_and_pressing_enter_closes_it_and_records_both_tags_in_the_drives_tags_db(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    Library.create(drive)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    enter_in_tag_prompt(qtbot, viewer, "beach family")

    assert visible_tag_prompt_texts(viewer) == []
    assert Library.open(drive).tags(folder / "IMG_1.png") == ["beach", "family"]


def test_on_a_file_tagged_beach_family_typing_minus_family_in_the_tag_prompt_and_pressing_enter_leaves_it_tagged_only_beach(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    Library.create(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    enter_in_tag_prompt(qtbot, viewer, "-family")

    assert Library.open(drive).tags(folder / "IMG_1.png") == ["beach"]


def test_pressing_t_again_after_closing_the_tag_prompt_shows_only_one_tag_prompt_with_one_copy_of_the_files_tags(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    Library.create(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    enter_in_tag_prompt(qtbot, viewer, "beach")

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert visible_tag_prompt_texts(viewer) == [""]
    assert shown_texts(viewer).count("beach family") == 1


def test_the_tag_prompt_is_drawn_inside_the_viewer_window_centred_horizontally_near_the_bottom_just_above_the_status_bar(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    Library.create(drive)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    viewer.resize(1600, 900)
    qtbot.waitUntil(lambda: viewer.width() == 1600)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    [prompt] = visible_tag_prompts(viewer)
    frame = QRect(prompt.mapTo(viewer, QPoint()), prompt.size())
    assert prompt.window() is viewer
    assert abs(frame.center().x() - viewer.rect().center().x()) <= 1
    assert viewer.height() * 3 // 4 <= frame.bottom() < viewer.status_bar.geometry().top()


def test_pressing_t_makes_the_tag_prompts_input_the_viewers_focus_widget(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    Library.create(drive)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    [prompt] = visible_tag_prompts(viewer)
    assert viewer.focusWidget() is prompt


def test_the_tag_prompts_input_and_its_shown_tags_are_styled_like_the_info_overlay(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    Library.create(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    [prompt] = visible_tag_prompts(viewer)
    [tags] = [label for label in shown_labels(viewer) if label.text() == "beach family"]
    assert [prompt.styleSheet(), tags.styleSheet()] == [viewer.info.styleSheet()] * 2


def test_typing_space_i_p_f_m_in_the_open_tag_prompt_goes_into_it_and_leaves_the_slideshow_and_info_overlay_unchanged(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    make_image(folder / "IMG_2.png", "blue")
    Library.create(drive)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_T)
    window_state = viewer.windowState()

    qtbot.keyClicks(viewer.focusWidget(), " ipfm")

    assert visible_tag_prompt_texts(viewer) == [" ipfm"]
    assert viewer.slideshow.current == folder / "IMG_1.png"
    assert not viewer.info.isVisible()
    assert viewer.windowState() == window_state


def test_typing_p_and_m_in_the_tag_prompt_open_over_a_playing_video_neither_pauses_nor_mutes_it(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Clips")
    make_clip(folder / "IMG_1.mp4", duration=30)
    Library.create(drive)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    wait_until_playing(engine)
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    qtbot.keyClicks(viewer.focusWidget(), "pm")

    assert visible_tag_prompt_texts(viewer) == ["pm"]
    assert [engine.pause, engine.mute] == [False, False]


def test_arrow_keys_in_the_tag_prompt_open_over_a_paused_video_neither_move_the_slideshow_nor_seek_it(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Clips")
    make_clip(folder / "IMG_1.mp4", duration=60)
    make_image(folder / "IMG_2.png", "red")
    Library.create(drive)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    wait_until_playing(engine)
    qtbot.keyClick(viewer, Qt.Key.Key_P)
    engine.time_pos = 20
    engine.wait_for_property("time-pos", lambda time_pos: time_pos == pytest.approx(20, abs=1), timeout=5)
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    for key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
        qtbot.keyClick(viewer.focusWidget(), key)
        qtbot.wait(300)  # mpv seeks asynchronously, so give a stray seek time to land

        assert viewer.slideshow.current == folder / "IMG_1.mp4"
        assert engine.time_pos == pytest.approx(20, abs=1)


def test_pressing_esc_in_the_tag_prompt_closes_it_leaving_the_viewer_open_and_the_files_tags_unchanged(qtbot, tmp_path):
    [drive] = make_folders(tmp_path, "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "red")
    Library.create(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_T)
    qtbot.keyClicks(viewer.focusWidget(), "-family sunset")

    qtbot.keyClick(viewer.focusWidget(), Qt.Key.Key_Escape)

    assert visible_tag_prompt_texts(viewer) == []
    assert Library.open(drive).tags(folder / "IMG_1.png") == ["beach", "family"]
    assert viewer.isVisible()
