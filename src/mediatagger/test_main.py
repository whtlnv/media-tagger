import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtGui import QColor

from mediatagger.test_video import make_clip
from mediatagger.test_viewer import make_image, offscreen_environment, run_python_offscreen, shown_launch_viewer, shown_texts, shown_viewer_on
from mediatagger.backup import back_up, newest_backup
from mediatagger.library import Library
from mediatagger.test_viewer_backup import tags_in_newest_backup
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image, drive_without_a_tag_library_holding_one_image, overwrite_tags_db_with_garbage
from mediatagger.drive_session import DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT

RUN_MEDIATAGGER_COMMAND = (
    "from importlib.metadata import entry_points\n"
    "(command,) = entry_points(group='console_scripts', name='mediatagger')\n"
    "command.load()()\n"
)

SILENCE_THE_VIEWERS_ENGINE = (
    "import mediatagger.viewer\n"
    "from mediatagger.test_viewer import SILENT\n"
    "unsilenced_engine = mediatagger.viewer.new_engine\n"
    "mediatagger.viewer.new_engine = lambda **options: unsilenced_engine(**{**options, **SILENT})\n"
)

REPORT_SHOWN_WINDOW_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.test_viewer import centre_colour\n"
    "app = QApplication([])\n"
    "def report():\n"
    "    for window in QApplication.topLevelWidgets():\n"
    "        if window.isVisible():\n"
    "            print(f'fullscreen={window.isFullScreen()} centre={centre_colour(window).name()}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, report)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND


def test_running_the_mediatagger_command_on_a_folder_opens_a_normal_not_fullscreen_viewer_on_its_first_item(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    result = run_python_offscreen(REPORT_SHOWN_WINDOW_SCRIPT, str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"fullscreen=False centre={QColor('red').name()}"


def test_the_installed_mediatagger_executable_started_on_its_own_keeps_running_with_its_viewer_open(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    executable = Path(sys.executable).parent / "mediatagger"
    process = subprocess.Popen(
        [str(executable), str(tmp_path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=offscreen_environment(),
    )
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    still_running = process.poll() is None
    process.kill()
    _, stderr = process.communicate()
    assert still_running, stderr


def test_running_the_mediatagger_command_on_a_file_opens_a_normal_not_fullscreen_viewer_on_that_file(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    make_image(tmp_path / "IMG_3.png", "green")
    result = run_python_offscreen(REPORT_SHOWN_WINDOW_SCRIPT, str(tmp_path / "IMG_2.png"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"fullscreen=False centre={QColor('blue').name()}"

PRESS_ESC_THEN_REPORT_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication, QListView\n"
    "app = QApplication([])\n"
    "def press_esc_then_report():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    QTest.keyClick(window, Qt.Key.Key_Escape)\n"
    "    shown = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    grids = [grid for grid in window.findChildren(QListView) if grid.isVisible()]\n"
    "    cursor = [grid.currentIndex().data() for grid in grids]\n"
    "    print(f'windows={len(shown)} cursor={cursor}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, press_esc_then_report)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND


def test_pressing_esc_in_the_slideshow_of_the_mediatagger_command_shows_that_folders_grid_in_the_same_window_with_the_cursor_on_the_shown_file(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    result = run_python_offscreen(PRESS_ESC_THEN_REPORT_SCRIPT, str(tmp_path / "IMG_2.png"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "windows=1 cursor=['IMG_2.png']"

REPORT_SHOWN_TEXTS_ON_TIMER = (
    "import sys\n"
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.test_viewer import shown_texts\n"
    "app = QApplication([])\n"
    "def report():\n"
    "    for window in QApplication.topLevelWidgets():\n"
    "        if window.isVisible():\n"
    "            for text in shown_texts(window):\n"
    "                print(text, flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, report)\n"
)

REPORT_SHOWN_TEXTS_WITH_NO_PATH_SCRIPT = (
    REPORT_SHOWN_TEXTS_ON_TIMER
    + "sys.argv = ['mediatagger']\n"
    + RUN_MEDIATAGGER_COMMAND
)


def test_running_the_mediatagger_command_with_no_path_opens_the_window_showing_the_launch_text(qtbot):
    launch_texts = shown_texts(shown_launch_viewer(qtbot))
    result = run_python_offscreen(REPORT_SHOWN_TEXTS_WITH_NO_PATH_SCRIPT)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == launch_texts

DROP_FOLDER_WITH_NO_PATH_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.test_viewer import centre_colour, shown_texts\n"
    "from mediatagger.test_viewer_open import drag_and_drop_onto\n"
    "app = QApplication([])\n"
    "folder = sys.argv[1]\n"
    "def drop_then_report():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    drag_and_drop_onto(window, folder)\n"
    "    colour = centre_colour(window).name()\n"
    "    texts = shown_texts(window)\n"
    "    print(f'centre={colour} texts={texts}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, drop_then_report)\n"
    "sys.argv = ['mediatagger']\n"
) + RUN_MEDIATAGGER_COMMAND


def test_dropping_a_folder_onto_the_mediatagger_command_started_with_no_path_starts_its_slideshow_at_its_first_item(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    result = run_python_offscreen(DROP_FOLDER_WITH_NO_PATH_SCRIPT, str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"centre={QColor('red').name()} texts=[]"

REPORT_SHOWN_TEXTS_SCRIPT = (
    REPORT_SHOWN_TEXTS_ON_TIMER
    + "sys.argv = ['mediatagger', sys.argv[1]]\n"
    + RUN_MEDIATAGGER_COMMAND
)


def test_running_the_mediatagger_command_on_a_path_that_does_not_exist_keeps_running_and_says_it_cant_open_it(qtbot):
    missing = Path("/no/such/path")
    cant_open_texts = shown_texts(shown_viewer_on(qtbot, missing))
    result = run_python_offscreen(REPORT_SHOWN_TEXTS_SCRIPT, str(missing))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == cant_open_texts

TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT = (
    "import os, sys\n"
    "drive = sys.argv[1]\n"
    "os.path.ismount = lambda path: os.fspath(path) == drive\n"
)

RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT = "sys.argv = ['mediatagger', sys.argv[2]]\n" + RUN_MEDIATAGGER_COMMAND

# The question comes up only once the viewer has settled, so poll for it rather than guess when.
ANSWER_THE_QUESTION_ONCE_ASKED = (
    "polling = QTimer()\n"
    "polling.timeout.connect(answer)\n"
    "polling.start(100)\n"
    "def report_soon():\n"
    "    polling.stop()\n"
    "    QTimer.singleShot(1000, report)\n"
    "QTimer.singleShot(10000, report_soon)\n"
)

DECLINE_CREATING_A_LIBRARY_SCRIPT = TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT + (
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.test_viewer import centre_colour\n"
    "from mediatagger.test_viewer_library import status_bar_texts\n"
    "app = QApplication([])\n"
    "asked = []\n"
    "def answer():\n"
    "    question = QApplication.activeModalWidget()\n"
    "    if question is not None:\n"
    "        asked.append(True)\n"
    "        question.reject()\n"
    "        report_soon()\n"
    "def report():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    print(f'asked={asked} centre={centre_colour(window).name()} status={status_bar_texts(window)}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    + ANSWER_THE_QUESTION_ONCE_ASKED
) + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT


def test_running_the_mediatagger_command_on_a_drive_without_a_tag_library_asks_and_declining_keeps_the_slideshow_saying_the_drive_has_no_tag_library(tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    result = run_python_offscreen(DECLINE_CREATING_A_LIBRARY_SCRIPT, str(drive), str(folder))
    assert result.returncode == 0, result.stderr
    no_library_status = [DRIVE_HAS_NO_LIBRARY_VIEWING_ONLY_TEXT.format(drive.name)]
    assert result.stdout.strip() == f"asked=[True] centre={QColor('red').name()} status={no_library_status}"

NOTE_WHETHER_THE_VIEWER_IS_SHOWN_WHEN_ASKED_SCRIPT = TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT + (
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.viewer import Viewer\n"
    "app = QApplication([])\n"
    "viewer_shown_when_asked = []\n"
    "def answer():\n"
    "    question = QApplication.activeModalWidget()\n"
    "    if question is not None:\n"
    "        shown = [widget for window in QApplication.topLevelWidgets() for widget in [window, *window.findChildren(Viewer)] if widget.isVisible()]\n"
    "        viewer_shown_when_asked.append(any(isinstance(widget, Viewer) for widget in shown))\n"
    "        question.reject()\n"
    "        report_soon()\n"
    "def report():\n"
    "    print(f'viewer_shown_when_asked={viewer_shown_when_asked}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    + ANSWER_THE_QUESTION_ONCE_ASKED
) + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT


def test_running_the_mediatagger_command_on_a_drive_without_a_tag_library_asks_to_create_one_over_the_already_shown_viewer(tmp_path):
    drive, folder = drive_without_a_tag_library_holding_one_image(tmp_path)
    result = run_python_offscreen(NOTE_WHETHER_THE_VIEWER_IS_SHOWN_WHEN_ASKED_SCRIPT, str(drive), str(folder))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "viewer_shown_when_asked=[True]"

ENTER_TAGS_IN_THE_TAG_PROMPT_SCRIPT = TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT + (
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication\n"
    "app = QApplication([])\n"
    "tags = sys.argv[3]\n"
    "def enter_tags():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    QTest.keyClick(window, Qt.Key.Key_T)\n"
    "    QTest.keyClicks(window.focusWidget(), tags)\n"
    "    QTest.keyClick(window.focusWidget(), Qt.Key.Key_Return)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, enter_tags)\n"
) + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT

REPORT_SHOWN_TEXTS_ON_A_DRIVE_SCRIPT = (
    TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT
    + REPORT_SHOWN_TEXTS_ON_TIMER
    + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT
)


def test_tags_entered_in_the_mediatagger_command_on_a_drive_with_a_tag_library_are_recorded_in_its_tags_db_and_shown_by_the_next_run(tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)

    entered = run_python_offscreen(ENTER_TAGS_IN_THE_TAG_PROMPT_SCRIPT, str(drive), str(folder), "beach")
    assert entered.returncode == 0, entered.stderr
    assert Library.open(drive).tags(folder / "IMG_1.png") == ["beach"]

    shown = run_python_offscreen(REPORT_SHOWN_TEXTS_ON_A_DRIVE_SCRIPT, str(drive), str(folder))
    assert shown.returncode == 0, shown.stderr
    assert shown.stdout.splitlines() == ["beach"]


def test_the_mediatagger_command_on_a_folder_whose_first_file_is_tagged_beach_sunset_shows_beach_above_sunset_in_the_viewers_tag_overlay(tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach sunset")

    shown = run_python_offscreen(REPORT_SHOWN_TEXTS_ON_A_DRIVE_SCRIPT, str(drive), str(folder))

    assert shown.returncode == 0, shown.stderr
    assert shown.stdout.splitlines() == ["beach", "sunset"]

REPORT_SUGGESTIONS_AFTER_TYPING_IN_THE_TAG_PROMPT_SCRIPT = TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT + (
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.test_tag_prompt import listed, visible_suggestion_lists\n"
    "app = QApplication([])\n"
    "typed = sys.argv[3]\n"
    "def type_then_report():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    QTest.keyClick(window, Qt.Key.Key_T)\n"
    "    QTest.keyClicks(window.focusWidget(), typed)\n"
    "    print(f'suggestions={[listed(suggestions) for suggestions in visible_suggestion_lists()]}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, type_then_report)\n"
) + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT


def test_running_the_mediatagger_command_on_a_drive_whose_library_has_beach_pressing_t_and_typing_b_shows_the_suggestion_popup_listing_beach(tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    make_image(folder / "IMG_2.png", "blue")
    result = run_python_offscreen(REPORT_SUGGESTIONS_AFTER_TYPING_IN_THE_TAG_PROMPT_SCRIPT, str(drive), str(folder / "IMG_2.png"), "b")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "suggestions=[['beach']]"

ANSWER_YES_TO_THE_QUESTION_THEN_REPORT_SHOWN_TEXTS_SCRIPT = TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT + (
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication, QMessageBox\n"
    "from mediatagger.test_viewer import shown_texts\n"
    "from mediatagger.viewer import Viewer\n"
    "app = QApplication([])\n"
    "viewer_shown_when_asked = []\n"
    "def answer():\n"
    "    question = QApplication.activeModalWidget()\n"
    "    if question is not None:\n"
    "        shown = [widget for window in QApplication.topLevelWidgets() for widget in [window, *window.findChildren(Viewer)] if widget.isVisible()]\n"
    "        viewer_shown_when_asked.append(any(isinstance(widget, Viewer) for widget in shown))\n"
    "        question.button(QMessageBox.StandardButton.Yes).click()\n"
    "        report_soon()\n"
    "def report():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    print(f'viewer_shown_when_asked={viewer_shown_when_asked}', flush=True)\n"
    "    for text in shown_texts(window):\n"
    "        print(text, flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    + ANSWER_THE_QUESTION_ONCE_ASKED
) + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT


def test_running_the_mediatagger_command_on_a_drive_whose_tags_db_is_garbage_with_a_backup_under_xdg_data_home_asks_to_restore_over_the_shown_viewer_and_yes_shows_the_restored_tags(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data-home"))
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    library.enter(folder / "IMG_1.png", "beach")
    back_up(library, clock=lambda: datetime(2026, 10, 9, 15, 30, tzinfo=timezone.utc))
    overwrite_tags_db_with_garbage(drive)
    result = run_python_offscreen(ANSWER_YES_TO_THE_QUESTION_THEN_REPORT_SHOWN_TEXTS_SCRIPT, str(drive), str(folder))
    assert result.returncode == 0, result.stderr
    asked, *shown = result.stdout.splitlines()
    assert asked == "viewer_shown_when_asked=[True]"
    assert shown == ["beach"]


def test_running_the_mediatagger_command_with_xdg_data_home_set_on_a_drive_with_a_library_leaves_a_backup_holding_the_entered_tag_under_its_drive_id_after_closing(tmp_path, monkeypatch):
    data_home = tmp_path / "data-home"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    drive_id = Library.open(drive).drive_id
    result = run_python_offscreen(ENTER_TAGS_IN_THE_TAG_PROMPT_SCRIPT, str(drive), str(folder), "beach")
    assert result.returncode == 0, result.stderr
    backup_root = data_home / "mediatagger" / "backups"
    assert newest_backup(backup_root, drive.name).path.parent == backup_root / drive_id
    assert tags_in_newest_backup(backup_root, drive, tmp_path / "restored", folder.relative_to(drive) / "IMG_1.png") == ["beach"]

REPORT_SHOWN_GRID_WITH_NO_PATH_ON_A_DRIVE_SCRIPT = TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT + (
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.grid import Grid\n"
    "app = QApplication([])\n"
    "def report():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    grids = [grid for grid in window.findChildren(Grid) if grid.isVisible()]\n"
    "    print(f'grids={[str(grid.folder) for grid in grids]} cursor={[grid.currentIndex().data() for grid in grids]}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, report)\n"
    "sys.argv = ['mediatagger']\n"
) + RUN_MEDIATAGGER_COMMAND


def test_running_the_mediatagger_command_with_no_path_after_a_folder_was_viewed_opens_that_folders_grid(tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewed = run_python_offscreen(REPORT_SHOWN_TEXTS_ON_A_DRIVE_SCRIPT, str(drive), str(folder))
    assert viewed.returncode == 0, viewed.stderr

    result = run_python_offscreen(REPORT_SHOWN_GRID_WITH_NO_PATH_ON_A_DRIVE_SCRIPT, str(drive))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"grids={[str(folder)]} cursor=['IMG_1.png']"

PRESS_ESC_TWICE_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication\n"
    "app = QApplication([])\n"
    "def press_esc_twice():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    QTest.keyClick(window, Qt.Key.Key_Escape)\n"
    "    QTest.keyClick(window, Qt.Key.Key_Escape)\n"
    "QTimer.singleShot(1000, press_esc_twice)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND + "print('exited', flush=True)\n"


def test_pressing_esc_in_the_slideshow_and_then_esc_in_the_grid_of_the_mediatagger_command_makes_it_exit_cleanly(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    result = run_python_offscreen(PRESS_ESC_TWICE_SCRIPT, str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "exited"

PRESS_ESC_THEN_REPORT_THE_FIRST_TILES_THUMBNAIL_ONCE_IT_ARRIVES_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication\n"
    "from mediatagger.grid import TILE_ROLE, Grid\n"
    "app = QApplication([])\n"
    "def first_tiles_thumbnail():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    (grid,) = [grid for grid in window.findChildren(Grid) if grid.isVisible()]\n"
    "    return grid.model().index(0, 0).data(TILE_ROLE).thumbnail\n"
    "def report():\n"
    "    polling.stop()\n"
    "    thumbnail = first_tiles_thumbnail()\n"
    "    if thumbnail is None:\n"
    "        print('thumbnail=None', flush=True)\n"
    "    else:\n"
    "        print(f'thumbnail={thumbnail.width()}x{thumbnail.height()} {thumbnail.pixelColor(thumbnail.rect().center()).name()}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "def report_once_arrived():\n"
    "    if first_tiles_thumbnail() is not None:\n"
    "        report()\n"
    "polling = QTimer()\n"
    "polling.timeout.connect(report_once_arrived)\n"
    "def press_esc_then_poll():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    QTest.keyClick(window, Qt.Key.Key_Escape)\n"
    "    polling.start(100)\n"
    "    QTimer.singleShot(10000, report)\n"
    "QTimer.singleShot(1000, press_esc_then_poll)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND


def test_the_grid_of_the_mediatagger_command_launched_on_a_folder_shows_a_generated_thumbnail_on_an_image_tile_after_esc(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red", width=1600, height=800)
    result = run_python_offscreen(PRESS_ESC_THEN_REPORT_THE_FIRST_TILES_THUMBNAIL_ONCE_IT_ARRIVES_SCRIPT, str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"thumbnail=400x200 {QColor('red').name()}"

TAG_A_FOLDER_IN_THE_GRID_THEN_OPEN_A_FILE_INSIDE_IT_AND_REPORT_THE_TAG_OVERLAY_SCRIPT = TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT + (
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication, QStackedWidget\n"
    "from mediatagger.test_viewer import shown_labels\n"
    "from mediatagger.test_viewer_library import frame_in, visible_tag_prompts\n"
    "app = QApplication([])\n"
    "tags = sys.argv[3]\n"
    "def shown():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    return window, window.findChild(QStackedWidget).currentWidget()\n"
    "def tag_the_folder_tile_then_open_a_file_inside_it():\n"
    "    window, grid = shown()\n"
    "    QTest.keyClick(grid, Qt.Key.Key_Escape)\n"
    "    window, grid = shown()\n"
    "    QTest.keyClick(grid, Qt.Key.Key_Left)\n"
    "    QTest.keyClick(grid, Qt.Key.Key_T)\n"
    "    (prompt,) = visible_tag_prompts(window)\n"
    "    QTest.keyClicks(prompt, tags)\n"
    "    QTest.keyClick(prompt, Qt.Key.Key_Return)\n"
    "    QTest.keyClick(grid, Qt.Key.Key_Return)\n"
    "    window, grid = shown()\n"
    "    QTest.keyClick(grid, Qt.Key.Key_Return)\n"
    "    QTimer.singleShot(1000, report)\n"
    "def brightest_in(image, frame):\n"
    "    columns = range(frame.left(), frame.right() + 1)\n"
    "    rows = range(frame.top(), frame.bottom() + 1)\n"
    "    return max(image.pixelColor(x, y).lightness() for x in columns for y in rows)\n"
    "def report():\n"
    "    window, viewer = shown()\n"
    "    image = viewer.grab().toImage()\n"
    "    for label in shown_labels(viewer):\n"
    "        print(f'{label.text()} brightest={brightest_in(image, frame_in(viewer, label))}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, tag_the_folder_tile_then_open_a_file_inside_it)\n"
) + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT


def test_in_the_mediatagger_command_entering_beach_for_a_folder_tile_in_the_grid_then_enter_on_a_file_inside_it_shows_beach_dimmed_in_the_viewers_tag_overlay(tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    (folder / "trip").mkdir()
    make_image(folder / "trip" / "IMG_1.png", "red")
    result = run_python_offscreen(TAG_A_FOLDER_IN_THE_GRID_THEN_OPEN_A_FILE_INSIDE_IT_AND_REPORT_THE_TAG_OVERLAY_SCRIPT, str(drive), str(folder), "beach")
    assert result.returncode == 0, result.stderr
    [shown] = result.stdout.splitlines()
    text, brightest = shown.split(" brightest=")
    assert text == "beach"
    assert int(brightest) < 255 - 60  # an own tag is drawn white; an inherited one well below it

REPORT_THE_PLAYING_VIDEO_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import QTimer\n"
    "from PySide6.QtWidgets import QApplication, QStackedWidget\n"
) + SILENCE_THE_VIEWERS_ENGINE + (
    "from mediatagger.test_viewer import make_surface_ready\n"
    "from mediatagger.video_controls import ProgressBar\n"
    "app = QApplication([])\n"
    "def shown():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    return window, window.findChild(QStackedWidget).currentWidget()\n"
    "def stand_in_for_the_video_surface_becoming_ready():\n"
    "    window, viewer = shown()\n"
    "    make_surface_ready(viewer)\n"
    "    QTimer.singleShot(1500, report)\n"
    "def report():\n"
    "    window, viewer = shown()\n"
    "    bars = [bar for bar in viewer.findChildren(ProgressBar) if bar.isVisible()]\n"
    "    totals = [bar.text().split(' / ')[-1] for bar in bars]\n"
    "    print(f'fullscreen={window.isFullScreen()} playing={viewer.video_player.engine.path} bars={totals}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, stand_in_for_the_video_surface_becoming_ready)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND


def test_running_the_mediatagger_command_on_a_relative_path_to_a_video_opens_a_normal_window_playing_it_with_the_progress_bar_shown(tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=65)
    result = subprocess.run(
        [sys.executable, "-c", REPORT_THE_PLAYING_VIDEO_SCRIPT, clip.name],
        capture_output=True, text=True, timeout=30,
        env=offscreen_environment(), cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"fullscreen=False playing={clip} bars=['1:05']"

SPEED_UP_THEN_PRESS_0_AND_REPORT_THE_SPEED_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication, QStackedWidget\n"
) + SILENCE_THE_VIEWERS_ENGINE + (
    "from mediatagger.test_viewer import make_surface_ready\n"
    "app = QApplication([])\n"
    "def shown_viewer():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    return window.findChild(QStackedWidget).currentWidget()\n"
    "def stand_in_for_the_video_surface_becoming_ready():\n"
    "    make_surface_ready(shown_viewer())\n"
    "    QTimer.singleShot(1500, speed_up_then_press_0)\n"
    "def speed_up_then_press_0():\n"
    "    viewer = shown_viewer()\n"
    "    QTest.keyClick(viewer, Qt.Key.Key_BracketRight)\n"
    "    sped_up = viewer.video_player.engine.speed\n"
    "    QTest.keyClick(viewer, Qt.Key.Key_0)\n"
    "    print(f'sped_up={sped_up} after_0={viewer.video_player.engine.speed}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, stand_in_for_the_video_surface_becoming_ready)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND


def test_in_the_mediatagger_command_on_a_video_pressing_close_bracket_then_0_plays_it_at_1x_again(tmp_path):
    clip = make_clip(tmp_path / "IMG_1.mp4", duration=30)
    result = run_python_offscreen(SPEED_UP_THEN_PRESS_0_AND_REPORT_THE_SPEED_SCRIPT, str(clip))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "sped_up=1.25 after_0=1.0"

SEARCH_FROM_THE_GRID_THEN_REPORT_THE_BREADCRUMB_AND_TILES_SCRIPT = TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT + (
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication, QLabel, QStackedWidget\n"
    "from mediatagger.test_grid import tile_names\n"
    "app = QApplication([])\n"
    "query = sys.argv[3]\n"
    "def shown():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    return window, window.findChild(QStackedWidget).currentWidget()\n"
    "def search_then_report():\n"
    "    window, viewer = shown()\n"
    "    QTest.keyClick(viewer, Qt.Key.Key_Escape)\n"
    "    window, grid = shown()\n"
    "    QTest.keyClick(grid, Qt.Key.Key_Slash)\n"
    "    QTest.keyClicks(window.focusWidget(), query)\n"
    "    QTest.keyClick(window.focusWidget(), Qt.Key.Key_Return)\n"
    "    window, results = shown()\n"
    "    crumbs = [label.text() for label in window.findChildren(QLabel) if label.isVisible() and label.text().startswith('Search')]\n"
    "    print(f'crumbs={crumbs} tiles={tile_names(results)}', flush=True)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, search_then_report)\n"
) + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT


def test_running_the_mediatagger_command_on_a_folder_of_a_drive_with_a_tagged_library_then_searching_from_its_grid_shows_the_search_breadcrumb_over_the_matching_items(tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    Library.open(drive).enter(folder / "IMG_2.png", "beach")
    result = run_python_offscreen(SEARCH_FROM_THE_GRID_THEN_REPORT_THE_BREADCRUMB_AND_TILES_SCRIPT, str(drive), str(folder), "beach")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "crumbs=['Search: beach'] tiles=['IMG_2.png']"

RENAME_A_TAG_FROM_THE_GRID_SCRIPT = TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT + (
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication, QStackedWidget\n"
    "app = QApplication([])\n"
    "typed = sys.argv[3]\n"
    "def shown():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    return window, window.findChild(QStackedWidget).currentWidget()\n"
    "def rename_from_the_grid():\n"
    "    window, viewer = shown()\n"
    "    QTest.keyClick(viewer, Qt.Key.Key_Escape)\n"
    "    window, grid = shown()\n"
    "    QTest.keyClick(grid, Qt.Key.Key_N)\n"
    "    QTest.keyClicks(window.focusWidget(), typed)\n"
    "    QTest.keyClick(window.focusWidget(), Qt.Key.Key_Return)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, rename_from_the_grid)\n"
) + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT


def test_in_the_mediatagger_command_on_a_drive_pressing_n_in_the_grid_typing_beach_places_beach_and_enter_renames_the_tag_in_the_drives_tags_db(tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach")
    result = run_python_offscreen(RENAME_A_TAG_FROM_THE_GRID_SCRIPT, str(drive), str(folder), "beach places:beach")
    assert result.returncode == 0, result.stderr
    assert Library.open(drive).tags(folder / "IMG_1.png") == ["places:beach"]

PRESS_ESC_THEN_O_IN_THE_GRID_THEN_REPORT_THE_PICKER_SCRIPT = (
    "import sys\n"
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication, QFileDialog, QListView\n"
    "app = QApplication([])\n"
    "def report_the_picker():\n"
    "    pickers = [widget for widget in QApplication.topLevelWidgets() if isinstance(widget, QFileDialog) and widget.isVisible()]\n"
    "    print(f'pickers={len(pickers)} folders={[picker.fileMode() == QFileDialog.FileMode.Directory for picker in pickers]}', flush=True)\n"
    "    for picker in pickers:\n"
    "        picker.reject()\n"
    "def press_esc_then_o_in_the_grid():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    QTest.keyClick(window, Qt.Key.Key_Escape)\n"
    "    (grid,) = [grid for grid in window.findChildren(QListView) if grid.isVisible()]\n"
    "    QTimer.singleShot(500, report_the_picker)\n"
    "    QTest.keyClick(grid, Qt.Key.Key_O)\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, press_esc_then_o_in_the_grid)\n"
    "sys.argv = ['mediatagger', sys.argv[1]]\n"
) + RUN_MEDIATAGGER_COMMAND


def test_pressing_o_in_the_grid_of_the_mediatagger_command_opens_its_folder_picker(tmp_path):
    make_image(tmp_path / "IMG_1.png", "red")
    make_image(tmp_path / "IMG_2.png", "blue")
    result = run_python_offscreen(PRESS_ESC_THEN_O_IN_THE_GRID_THEN_REPORT_THE_PICKER_SCRIPT, str(tmp_path / "IMG_2.png"))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "pickers=1 folders=[True]"
