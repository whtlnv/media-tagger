from mediatagger.library import Library
from mediatagger.test_library import _read_meta, create_schema_version_2_library
from mediatagger.test_main import REPORT_SHOWN_TEXTS_ON_A_DRIVE_SCRIPT, RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT, TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT
from mediatagger.test_viewer import make_image, run_python_offscreen
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_clip

ON_THE_PLAYING_VIDEO = TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT + (
    "from PySide6.QtCore import Qt, QTimer\n"
    "from PySide6.QtTest import QTest\n"
    "from PySide6.QtWidgets import QApplication, QStackedWidget\n"
    "import mediatagger.viewer\n"
    "from mediatagger.test_viewer import SILENT, make_surface_ready\n"
    "unsilenced_engine = mediatagger.viewer.new_engine\n"
    "mediatagger.viewer.new_engine = lambda **options: unsilenced_engine(**{**options, **SILENT})\n"
    "app = QApplication([])\n"
    "def shown_viewer():\n"
    "    (window,) = [window for window in QApplication.topLevelWidgets() if window.isVisible()]\n"
    "    return window.findChild(QStackedWidget).currentWidget()\n"
    "def stand_in_for_the_video_surface_becoming_ready():\n"
    "    make_surface_ready(shown_viewer())\n"
    "    QTimer.singleShot(1500, lambda: then(shown_viewer()))\n"
    "def quit():\n"
    "    QApplication.closeAllWindows()\n"
    "    QApplication.quit()\n"
    "QTimer.singleShot(1000, stand_in_for_the_video_surface_becoming_ready)\n"
)

ADD_A_CHAPTER_SCRIPT = ON_THE_PLAYING_VIDEO.replace("app = QApplication([])\n", (
    "app = QApplication([])\n"
    "typed = sys.argv[3]\n"
    "def then(viewer):\n"
    "    QTest.keyClick(viewer, Qt.Key.Key_C)\n"
    "    QTest.keyClicks(viewer.tag_prompt.input, typed)\n"
    "    QTest.keyClick(viewer.tag_prompt.input, Qt.Key.Key_Return)\n"
    "    quit()\n"
)) + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT

REPORT_THE_CHAPTER_LIST_SCRIPT = ON_THE_PLAYING_VIDEO.replace("app = QApplication([])\n", (
    "from mediatagger.test_chapters import shown_chapter_lines\n"
    "app = QApplication([])\n"
    "def then(viewer):\n"
    "    QTest.keyClick(viewer, Qt.Key.Key_L)\n"
    "    print(f'chapters={shown_chapter_lines(viewer)}', flush=True)\n"
    "    quit()\n"
)) + RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT


def test_a_chapter_added_with_c_in_the_mediatagger_command_is_recorded_in_the_drives_tags_db_and_listed_by_l_in_the_next_run(tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=30)

    added = run_python_offscreen(ADD_A_CHAPTER_SCRIPT, str(drive), str(folder), "goal")
    assert added.returncode == 0, added.stderr
    [moment] = Library.open(drive).moments(folder / "IMG_1.mp4")
    assert moment.tags == ["goal"]

    listed = run_python_offscreen(REPORT_THE_CHAPTER_LIST_SCRIPT, str(drive), str(folder))
    assert listed.returncode == 0, listed.stderr
    assert listed.stdout.splitlines() == [f"chapters=['0:{round(moment.seconds):02d} goal']"]


def test_the_mediatagger_command_on_a_drive_whose_library_is_at_schema_version_2_upgrades_it_and_shows_its_tags(tmp_path):
    drive = tmp_path / "MEDIATAGGER"
    (drive / "Photos").mkdir(parents=True)
    make_image(drive / "Photos" / "IMG_1.png", "red")
    create_schema_version_2_library(drive, "phase-17-drive", {"Photos/IMG_1.png": ("file", ["beach", "family"])})

    shown = run_python_offscreen(REPORT_SHOWN_TEXTS_ON_A_DRIVE_SCRIPT, str(drive), str(drive / "Photos"))

    assert shown.returncode == 0, shown.stderr
    assert shown.stdout.splitlines() == ["beach family"]
    assert _read_meta(drive)["schema_version"] == "3"  # read as stored: opening a Library would upgrade it itself
