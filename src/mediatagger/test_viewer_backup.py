import shutil
from datetime import datetime, timezone

from mediatagger.backup import newest_backup
from mediatagger.library import Library, tags_db_path
from mediatagger.test_viewer import make_image, SILENT
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, make_tag_library_drive, overwrite_tags_db_with_garbage, status_bar_texts
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders
from mediatagger.viewer import BACKING_UP_TEXT, Viewer


def viewer_backing_up_into(qtbot, backup_root, folder, *drives):
    viewer = Viewer(
        folder, player_options=SILENT, is_mount_point=lambda path: path in drives,
        ask_to_create_library=lambda question: False, backup_root=backup_root,
    )
    qtbot.addWidget(viewer)
    return viewer


def show_and_tag(qtbot, viewer, tag):
    viewer.resize(400, 300)
    viewer.show()
    qtbot.waitExposed(viewer)
    enter_in_tag_prompt(qtbot, viewer, tag)


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

    viewer = Viewer(
        folder, player_options=SILENT, is_mount_point=lambda path: path == drive,
        backup_root=tmp_path / "backups", backup_clock=clock_noting_the_status_bar,
    )
    qtbot.addWidget(viewer)

    viewer.close()

    assert BACKING_UP_TEXT in status_while_backing_up[-1]
