from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel

import mediatagger
from mediatagger.library import Library
from mediatagger.test_video import make_clip
from mediatagger.test_viewer import centre_colour, make_image, shown_labels, shown_launch_viewer, shown_texts, shown_viewer_on, SILENT, shows_video_surface
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders
from mediatagger.viewer import (
    CORNER_MARGIN, CREATE_LIBRARY_QUESTION, DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT, LIBRARY_TEXT, NO_LIBRARY_TEXT, NO_LIBRARY_VIEWING_ONLY_TEXT,
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


def app_runs_from(drive, monkeypatch):
    monkeypatch.setattr(mediatagger, "__file__", str(drive / "app" / "mediatagger" / "__init__.py"))


def viewer_on_drive(qtbot, folder, drive, ask_to_create_library):
    viewer = Viewer(
        folder, player_options=SILENT, is_mount_point=lambda path: path == drive,
        ask_to_create_library=ask_to_create_library,
    )
    qtbot.addWidget(viewer)
    return viewer


def shown_viewer_on_drive(qtbot, folder, drive, ask_to_create_library):
    viewer = viewer_on_drive(qtbot, folder, drive, ask_to_create_library)
    viewer.resize(400, 300)
    viewer.show()
    qtbot.waitExposed(viewer)
    return viewer


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
    assert status_bar_texts(viewer) == [NO_LIBRARY_VIEWING_ONLY_TEXT]


def test_opening_a_folder_on_the_drive_the_app_runs_from_never_asks_to_create_a_library_writes_nothing_and_says_no_library_viewing_only(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    app_runs_from(drive, monkeypatch)
    asked = []

    def decline(question):
        asked.append(question)
        return False

    viewer = viewer_on_drive(qtbot, folder, drive, decline)

    assert asked == []
    assert not (drive / ".mediatagger").exists()
    assert status_bar_texts(viewer) == [NO_LIBRARY_VIEWING_ONLY_TEXT]


def test_opening_a_folder_on_the_drive_the_app_runs_from_that_already_has_a_tag_library_does_not_open_it_and_says_no_library_viewing_only(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    app_runs_from(drive, monkeypatch)

    viewer = viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert status_bar_texts(viewer) == [NO_LIBRARY_VIEWING_ONLY_TEXT]


def test_opening_a_folder_on_a_drive_without_a_tag_library_asks_to_create_one_on_that_drive_before_writing_to_it(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    asked = []

    def decline_noting_whether_the_drive_was_written(question):
        asked.append((question, (drive / ".mediatagger").exists()))
        return False

    viewer_on_drive(qtbot, folder, drive, decline_noting_whether_the_drive_was_written)

    assert asked == [(CREATE_LIBRARY_QUESTION.format("MEDIATAGGER"), False)]


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


def test_accepting_to_create_a_tag_library_on_a_drive_creates_a_real_library_whose_tags_db_reports_a_drive_id(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)

    viewer_on_drive(qtbot, folder, drive, lambda question: True)

    assert Library.open(drive).drive_id


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

    def decline(question):
        asked.append(question)
        return False

    viewer = viewer_on_drive(qtbot, folder, drive, decline)
    drag_and_drop_onto(viewer, other)

    assert asked == [CREATE_LIBRARY_QUESTION.format("MEDIATAGGER")]


def test_opening_a_folder_that_does_not_exist_on_a_drive_without_a_tag_library_does_not_ask_to_create_one(qtbot, tmp_path):
    drive, _ = drive_without_a_tag_library_holding_one_image(tmp_path)
    asked = []

    def decline(question):
        asked.append(question)
        return False

    viewer = shown_viewer_on_drive(qtbot, drive / "Holidays", drive, decline)

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
    placeholder_shown_when_asked = []
    viewer = Viewer(
        player_options=SILENT, is_mount_point=lambda path: path == drive,
        ask_to_create_library=lambda question: placeholder_shown_when_asked.append(shown_texts(viewer)),
    )
    qtbot.addWidget(viewer)
    viewer.show()
    qtbot.waitExposed(viewer)

    drag_and_drop_onto(viewer, folder)

    assert placeholder_shown_when_asked == [[]]


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

    def decline(question):
        asked.append(question)
        return False

    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, decline)
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
        viewer = Viewer(
            viewed, player_options=SILENT, is_mount_point=lambda path: path in (read_only_drive, writable_drive),
            ask_to_create_library=lambda question: False,
        )
        qtbot.addWidget(viewer)
        viewer.resize(400, 300)
        viewer.show()
        qtbot.waitExposed(viewer)

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
        viewer = Viewer(
            viewed, player_options=SILENT, is_mount_point=lambda path: path in (viewed_drive, read_only_drive),
            ask_to_create_library=lambda question: False,
        )
        qtbot.addWidget(viewer)

        drag_and_drop_onto(viewer, dropped)
        status = status_bar_texts(viewer)

    assert READ_ONLY_STATUS_TEXT in status
    assert LIBRARY_TEXT.format("BACKUP") not in status
