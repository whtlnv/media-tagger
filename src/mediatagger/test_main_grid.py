from PySide6.QtGui import QColor

from mediatagger.library import Library
from mediatagger.test_main import RUN_MEDIATAGGER_COMMAND, RUN_MEDIATAGGER_COMMAND_ON_THE_SECOND_ARGUMENT, TREAT_FIRST_ARGUMENT_AS_A_MOUNT_POINT
from mediatagger.test_viewer import make_image, run_python_offscreen
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image

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
