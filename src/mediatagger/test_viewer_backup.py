import shutil

from mediatagger.backup import newest_backup
from mediatagger.library import Library, tags_db_path
from mediatagger.test_viewer import SILENT
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, overwrite_tags_db_with_garbage
from mediatagger.viewer import Viewer


def test_opening_a_folder_on_a_drive_whose_library_opens_backs_up_that_drives_database_into_the_backup_root(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"

    viewer = Viewer(
        folder, player_options=SILENT, is_mount_point=lambda path: path == drive,
        ask_to_create_library=lambda question: False, backup_root=backup_root,
    )
    qtbot.addWidget(viewer)

    backup = newest_backup(backup_root, drive.name)
    assert backup is not None
    assert backup.path.parent.name == Library.open(drive).drive_id


def test_opening_a_folder_on_a_drive_whose_library_cant_be_opened_makes_no_backup(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    overwrite_tags_db_with_garbage(drive)
    backup_root = tmp_path / "backups"

    viewer = Viewer(
        folder, player_options=SILENT, is_mount_point=lambda path: path == drive,
        ask_to_create_library=lambda question: False, backup_root=backup_root,
    )
    qtbot.addWidget(viewer)

    assert newest_backup(backup_root, drive.name) is None


def test_closing_the_viewer_after_tagging_an_item_leaves_a_backup_containing_that_tag_written_before_the_close_returns(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    backup_root = tmp_path / "backups"
    viewer = Viewer(
        folder, player_options=SILENT, is_mount_point=lambda path: path == drive,
        ask_to_create_library=lambda question: False, backup_root=backup_root,
    )
    qtbot.addWidget(viewer)
    viewer.resize(400, 300)
    viewer.show()
    qtbot.waitExposed(viewer)
    enter_in_tag_prompt(qtbot, viewer, "sunset")

    viewer.close()

    restored_drive = tmp_path / "restored"
    tags_db_path(restored_drive).parent.mkdir(parents=True)
    shutil.copy(newest_backup(backup_root, drive.name).path, tags_db_path(restored_drive))
    assert Library.open(restored_drive).tags(restored_drive / "Photos" / "IMG_1.png") == ["sunset"]
