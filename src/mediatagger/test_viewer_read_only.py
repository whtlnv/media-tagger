from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from mediatagger.library import Library
from mediatagger.test_viewer import centre_colour, make_image, shown_labels, shown_texts
from mediatagger.test_viewer_library import (
    decline_noting_the_question_in, drive_with_a_tag_library_holding_one_image, drive_without_a_tag_library_holding_one_image, frame_in, made_read_only, make_tag_library_drive,
    resize_and_wait, shown_viewer_on_drive, shown_viewer_on_drives, status_bar_labels, status_bar_texts, viewer_on_drives, visible_tag_prompts,
)
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders
from mediatagger.drive_session import LIBRARY_TEXT
from mediatagger.status_bar import CORNER_MARGIN, READ_ONLY_STATUS_TEXT, TAGS_CANT_BE_SAVED_HERE_TEXT
from mediatagger.viewer import READ_ONLY_BANNER_TEXT


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

    frames = sorted((frame_in(viewer, label) for label in status_bar_labels(viewer)), key=lambda frame: frame.left())
    assert len(frames) >= 2  # the library and read-only texts, plus any background-work message
    assert all(viewer.rect().contains(frame) for frame in frames)
    assert frames[0].left() >= CORNER_MARGIN
    assert max(frame.bottom() for frame in frames) <= viewer.rect().bottom() - CORNER_MARGIN
    assert all(left.right() < right.left() for left, right in zip(frames, frames[1:]))


def test_on_a_read_only_drive_with_a_tag_library_each_status_bar_text_is_styled_like_the_info_overlay(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    shown = status_bar_labels(viewer)
    assert len(shown) >= 2  # the library and read-only texts, plus any background-work message
    assert [label.styleSheet() for label in shown] == [viewer.info.styleSheet()] * len(shown)


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
    resize_and_wait(qtbot, viewer, 1600, 900)

    [banner] = shown_labels(viewer)
    frame = frame_in(viewer, banner)
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


def test_pressing_t_on_a_read_only_drive_with_a_tag_library_opens_no_tag_prompt(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

        qtbot.keyClick(viewer, Qt.Key.Key_T)

        assert visible_tag_prompts(viewer) == []


def test_on_a_read_only_drive_with_a_tag_library_the_tag_overlay_still_shows_a_files_existing_tags(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

        assert sorted(shown_texts(viewer)) == sorted([READ_ONLY_BANNER_TEXT, "beach family"])


def test_pressing_t_on_a_read_only_drive_with_a_tag_library_says_tags_cant_be_saved_here_in_the_status_bar(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

        qtbot.keyClick(viewer, Qt.Key.Key_T)

        assert TAGS_CANT_BE_SAVED_HERE_TEXT in status_bar_texts(viewer)
