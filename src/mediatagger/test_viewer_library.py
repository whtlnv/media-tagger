import sqlite3
from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel, QLineEdit

from mediatagger.library import Library, tags_db_path
from mediatagger.test_video import make_clip
from mediatagger.test_viewer import centre_colour, make_image, show_exposed, shown_labels, shown_launch_viewer, shown_texts, shown_viewer_on, SILENT, shows_video_surface
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders
from mediatagger.viewer import (
    APP_PACKAGE, CREATE_LIBRARY_QUESTION, DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT, LIBRARY_TEXT, NO_LIBRARY_TEXT, NO_LIBRARY_VIEWING_ONLY_TEXT,
    TAGS_CANT_BE_SAVED_HERE_TEXT, Viewer,
)


def status_bar_labels(viewer):
    return [label for label in viewer.status_bar.findChildren(QLabel) if not label.isHidden()]


def status_bar_texts(viewer):
    return [label.text() for label in status_bar_labels(viewer)]


def frame_in(viewer, widget):
    return QRect(widget.mapTo(viewer, QPoint()), widget.size())


def resize_and_wait(qtbot, viewer, width, height):
    viewer.resize(width, height)
    qtbot.waitUntil(lambda: viewer.width() == width)


def make_tag_library_drive(drive):
    drive.mkdir(parents=True)
    Library.create(drive)
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


def overwrite_tags_db_with_garbage(drive):
    tags_db_path(drive).write_bytes(b"this is not a database" * 100)


def drive_with_a_tag_library_holding_one_clip(tmp_path, **clip_options):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    [folder] = make_folders(drive, "Clips")
    make_clip(folder / "IMG_1.mp4", **clip_options)
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


def shown_viewer_on_drives(qtbot, folder, drives, ask_to_create_library, app_location=APP_PACKAGE):
    viewer = viewer_on_drives(qtbot, folder, drives, ask_to_create_library, app_location)
    show_exposed(qtbot, viewer)
    return viewer


def shown_viewer_on_drive(qtbot, folder, drive, ask_to_create_library, app_location=APP_PACKAGE):
    return shown_viewer_on_drives(qtbot, folder, (drive,), ask_to_create_library, app_location)


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

    assert LIBRARY_TEXT.format("MEDIATAGGER") in status_bar_texts(viewer)


def test_opening_a_folder_that_is_itself_a_drives_mount_point_with_a_tag_library_names_that_folder_in_the_status_bar(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    make_image(drive / "IMG_1.png", "red")

    viewer = viewer_on_drive(qtbot, drive, drive, lambda question: False)

    assert LIBRARY_TEXT.format("MEDIATAGGER") in status_bar_texts(viewer)


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

    assert LIBRARY_TEXT.format("BACKUP") in status_bar_texts(viewer)
    assert LIBRARY_TEXT.format("MEDIATAGGER") not in status_bar_texts(viewer)


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
    assert LIBRARY_TEXT.format("MEDIATAGGER") in status_bar_texts(viewer)


def test_accepting_to_create_a_tag_library_on_a_drive_whose_mediatagger_folder_holds_no_tags_db_creates_it_there_and_names_the_drive(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    (drive / ".mediatagger").mkdir()

    viewer = viewer_on_drive(qtbot, folder, drive, lambda question: True)

    assert (drive / ".mediatagger" / "tags.db").is_file()
    assert LIBRARY_TEXT.format("MEDIATAGGER") in status_bar_texts(viewer)


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
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path)

    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.waitUntil(lambda: shows_video_surface(viewer))

    status_text_centre = viewer.library_label.mapTo(viewer, viewer.library_label.rect().center())
    assert viewer.childAt(status_text_centre) is viewer.library_label


def test_pressing_t_on_a_drive_whose_tag_library_was_declined_opens_no_tag_prompt(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert visible_tag_prompts(viewer) == []


def test_pressing_t_on_a_folder_on_the_system_disk_opens_no_tag_prompt(qtbot, tmp_path):
    folder = tmp_path / "Photos"
    folder.mkdir()
    make_image(folder / "IMG_1.png", "red")
    viewer = shown_viewer_on_drive(qtbot, folder, Path("/"), lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert visible_tag_prompts(viewer) == []


def file_contents_under(root):
    return {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_pressing_t_on_the_drive_the_app_runs_from_opens_no_tag_prompt_and_writes_nothing_to_that_drive(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    before = file_contents_under(drive)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False, app_package_on(drive))

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert visible_tag_prompts(viewer) == []
    assert file_contents_under(drive) == before


def test_pressing_t_on_a_drive_whose_tag_library_was_declined_says_tags_cant_be_saved_here_in_the_status_bar(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert "Tags can't be saved here" in status_bar_texts(viewer)


def test_the_tags_cant_be_saved_here_message_leaves_the_status_bar_a_few_seconds_after_it_appears_while_the_library_status_stays(qtbot, tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    qtbot.waitUntil(lambda: TAGS_CANT_BE_SAVED_HERE_TEXT not in status_bar_texts(viewer), timeout=10000)

    assert status_bar_texts(viewer) == [DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT.format("MEDIATAGGER")]


def test_opening_a_folder_on_a_drive_whose_tags_db_is_garbage_still_shows_the_slideshow_and_says_the_library_cant_be_opened_viewing_only(qtbot, tmp_path):
    from mediatagger.viewer import LIBRARY_CANT_BE_OPENED_TEXT
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    overwrite_tags_db_with_garbage(drive)

    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert centre_colour(viewer) == QColor("red")
    assert status_bar_texts(viewer) == [LIBRARY_CANT_BE_OPENED_TEXT.format("MEDIATAGGER")]


def test_pressing_t_on_a_drive_whose_library_cant_be_opened_opens_no_tag_prompt_says_tags_cant_be_saved_here_and_leaves_the_drive_unchanged(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    overwrite_tags_db_with_garbage(drive)
    before = file_contents_under(drive)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert visible_tag_prompts(viewer) == []
    assert TAGS_CANT_BE_SAVED_HERE_TEXT in status_bar_texts(viewer)
    assert file_contents_under(drive) == before


def test_opening_a_folder_on_a_drive_whose_library_open_fails_with_an_os_error_still_shows_the_slideshow_and_says_the_library_cant_be_opened_viewing_only(qtbot, tmp_path, monkeypatch):
    from mediatagger.viewer import LIBRARY_CANT_BE_OPENED_TEXT
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")

    def open_on_an_unplugged_drive(root):
        raise OSError("drive was unplugged")

    monkeypatch.setattr(Library, "open", open_on_an_unplugged_drive)

    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert centre_colour(viewer) == QColor("red")
    assert status_bar_texts(viewer) == [LIBRARY_CANT_BE_OPENED_TEXT.format("MEDIATAGGER")]
