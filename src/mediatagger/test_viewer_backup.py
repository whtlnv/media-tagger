import errno
import os
import shutil
from datetime import datetime, timezone

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QLabel

from mediatagger.backup import back_up, default_backup_root, newest_backup
from mediatagger.library import Library, tags_db_path
from mediatagger.test_viewer import make_image, SILENT
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, make_tag_library_drive, overwrite_tags_db_with_garbage, status_bar_texts
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders
from mediatagger.viewer import BACKED_UP_TEXT, BACKING_UP_TEXT, BACKUP_FAILED_TEXT, Viewer


def viewer_backing_up_into(qtbot, backup_root, folder, *drives, **options):
    viewer = Viewer(
        folder, player_options=SILENT, is_mount_point=lambda path: path in drives,
        ask_to_create_library=lambda question: False, backup_root=backup_root, **options,
    )
    qtbot.addWidget(viewer)
    return viewer


def show_and_tag(qtbot, viewer, tag):
    viewer.resize(400, 300)
    viewer.show()
    qtbot.waitExposed(viewer)
    enter_in_tag_prompt(qtbot, viewer, tag)


class PaintedTexts(QObject):
    def __init__(self, labels):
        super().__init__()
        self.texts = []
        for label in labels:
            label.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Paint:
            self.texts.append(watched.text())
        return False


def tags_in_newest_backup(backup_root, drive, restored_drive, item):
    tags_db_path(restored_drive).parent.mkdir(parents=True)
    shutil.copy(newest_backup(backup_root, drive.name).path, tags_db_path(restored_drive))
    return Library.open(restored_drive).tags(restored_drive / item)


def test_opening_a_folder_on_a_drive_whose_library_opens_backs_up_that_drives_database_into_the_backup_root(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"

    viewer_backing_up_into(qtbot, backup_root, folder, drive)

    backup = newest_backup(backup_root, drive.name)
    assert backup is not None
    assert backup.path.parent.name == Library.open(drive).drive_id


def test_opening_a_folder_on_a_drive_whose_library_cant_be_opened_makes_no_backup(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    overwrite_tags_db_with_garbage(drive)
    backup_root = tmp_path / "backups"

    viewer_backing_up_into(qtbot, backup_root, folder, drive)

    assert newest_backup(backup_root, drive.name) is None


def test_closing_the_viewer_after_tagging_an_item_leaves_a_backup_containing_that_tag_written_before_the_close_returns(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    viewer = viewer_backing_up_into(qtbot, backup_root, folder, drive)
    show_and_tag(qtbot, viewer, "sunset")

    viewer.close()

    assert tags_in_newest_backup(backup_root, drive, tmp_path / "restored", "Photos/IMG_1.png") == ["sunset"]


def test_opening_a_folder_on_another_drive_after_tagging_an_item_leaves_a_backup_of_the_first_drive_containing_that_tag(qtbot, tmp_path):
    first_drive, viewed = drive_with_a_tag_library_holding_one_image(tmp_path)
    second_drive = make_tag_library_drive(tmp_path / "BACKUP")
    [dropped] = make_folders(second_drive, "Videos")
    make_image(dropped / "IMG_1.png", "green")
    backup_root = tmp_path / "backups"
    viewer = viewer_backing_up_into(qtbot, backup_root, viewed, first_drive, second_drive)
    show_and_tag(qtbot, viewer, "sunset")

    drag_and_drop_onto(viewer, dropped)

    assert tags_in_newest_backup(backup_root, first_drive, tmp_path / "restored", "Photos/IMG_1.png") == ["sunset"]


def test_while_a_backup_is_running_the_status_bar_shows_backing_up_database(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    status_while_backing_up = []
    viewer = None

    def clock_noting_the_status_bar():
        if viewer is not None:
            status_while_backing_up.append(status_bar_texts(viewer))
        return datetime(2026, 10, 9, 15, 30, tzinfo=timezone.utc)

    viewer = viewer_backing_up_into(qtbot, tmp_path / "backups", folder, drive, backup_clock=clock_noting_the_status_bar)

    viewer.close()

    assert BACKING_UP_TEXT in status_while_backing_up[-1]


def test_when_a_backup_finishes_the_status_bar_shows_backed_up(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)

    viewer = viewer_backing_up_into(qtbot, tmp_path / "backups", folder, drive)

    assert BACKED_UP_TEXT in status_bar_texts(viewer)


def test_on_a_shown_viewer_the_signed_backing_up_message_is_painted_before_the_backup_runs_and_the_signed_backed_up_message_follows(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    painted = None
    painted_when_backup_ran = []

    def clock_noting_what_was_painted():
        if painted is not None:
            painted_when_backup_ran.append(list(painted.texts))
        return datetime(2026, 10, 9, 15, 30, tzinfo=timezone.utc)

    viewer = viewer_backing_up_into(qtbot, tmp_path / "backups", folder, drive, backup_clock=clock_noting_what_was_painted)
    viewer.resize(400, 300)
    viewer.show()
    qtbot.waitExposed(viewer)
    painted = PaintedTexts(viewer.status_bar.findChildren(QLabel))

    viewer.close()

    assert "⟳ Backing up database…" in painted_when_backup_ran[-1]
    assert "✓ Backed up" in status_bar_texts(viewer)


def test_a_few_seconds_after_a_backup_finishes_backed_up_is_cleared_from_the_status_bar(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)

    viewer = viewer_backing_up_into(qtbot, tmp_path / "backups", folder, drive)

    qtbot.waitUntil(lambda: BACKED_UP_TEXT not in status_bar_texts(viewer), timeout=10000)


def test_when_a_backup_fails_because_the_backup_root_is_not_writable_the_status_bar_shows_backup_failed_with_its_reason_and_the_viewer_keeps_showing_the_item(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    backup_root.mkdir()
    backup_root.chmod(0o500)
    try:
        viewer = viewer_backing_up_into(qtbot, backup_root, folder, drive)
    finally:
        backup_root.chmod(0o700)

    assert BACKUP_FAILED_TEXT.format(os.strerror(errno.EACCES)) in status_bar_texts(viewer)
    assert viewer.slideshow.current == folder / "IMG_1.png"


def test_when_a_backup_fails_tagging_the_current_item_still_saves_its_tags(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    drives_backup_folder = backup_root / Library.open(drive).drive_id
    drives_backup_folder.mkdir(parents=True)
    drives_backup_folder.chmod(0o500)
    try:
        viewer = viewer_backing_up_into(qtbot, backup_root, folder, drive)
        show_and_tag(qtbot, viewer, "sunset")
    finally:
        drives_backup_folder.chmod(0o700)

    assert Library.open(drive).tags(folder / "IMG_1.png") == ["sunset"]


def test_building_a_viewer_on_a_drive_whose_library_opens_runs_no_timer_already_due_before_it_returns(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    fired_during_construction = []
    QTimer.singleShot(0, lambda: fired_during_construction.append(True))  # like a caller's timer that expects the viewer shown

    viewer_backing_up_into(qtbot, tmp_path / "backups", folder, drive)

    assert fired_during_construction == []


def test_when_writing_the_drives_drive_json_fails_during_a_backup_the_status_bar_shows_backup_failed_with_its_reason_and_the_viewer_keeps_showing_the_item(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    (backup_root / Library.open(drive).drive_id / "drive.json").mkdir(parents=True)

    viewer = viewer_backing_up_into(qtbot, backup_root, folder, drive)

    assert BACKUP_FAILED_TEXT.format(os.strerror(errno.EISDIR)) in status_bar_texts(viewer)
    assert viewer.slideshow.current == folder / "IMG_1.png"


def test_opening_a_folder_on_a_drive_whose_tags_db_is_garbage_with_backups_for_a_drive_of_the_same_name_asks_to_restore_the_newest_backup(qtbot, tmp_path):
    from mediatagger.viewer import RESTORE_LIBRARY_QUESTION

    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    taken_at = datetime(2026, 10, 9, 15, 30, tzinfo=timezone.utc)
    back_up(Library.open(drive), backup_root, clock=lambda: taken_at)
    overwrite_tags_db_with_garbage(drive)
    asked = []

    viewer_backing_up_into(qtbot, backup_root, folder, drive, ask_to_restore_library=lambda question: asked.append(question) or False)

    assert asked == [RESTORE_LIBRARY_QUESTION.format(drive.name, taken_at)]


def test_a_viewer_given_no_backup_root_finds_restore_backups_under_the_default_backup_root(qtbot, tmp_path):
    from mediatagger.viewer import RESTORE_LIBRARY_QUESTION

    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    taken_at = datetime(2026, 10, 9, 15, 30, tzinfo=timezone.utc)
    back_up(Library.open(drive), default_backup_root(), clock=lambda: taken_at)
    overwrite_tags_db_with_garbage(drive)
    asked = []

    viewer = Viewer(
        folder, player_options=SILENT, is_mount_point=lambda path: path == drive,
        ask_to_create_library=lambda question: False, ask_to_restore_library=lambda question: asked.append(question) or False,
    )
    qtbot.addWidget(viewer)

    assert asked == [RESTORE_LIBRARY_QUESTION.format(drive.name, taken_at)]
