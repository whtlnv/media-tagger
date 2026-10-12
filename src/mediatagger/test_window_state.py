import json
import os
import shutil
from pathlib import Path

import pytest
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QStackedWidget

from mediatagger.grid import TAG_BADGE, Grid
from mediatagger.library import Library
from mediatagger.test_grid import painted_texts
from mediatagger.test_viewer import SILENT, show_exposed
from mediatagger.test_viewer_library import drive_with_a_tag_library_holding_one_image
from mediatagger.test_viewer_open import drag_and_drop_onto
from mediatagger.test_window import shown_status_bar_texts
from mediatagger.viewer import Viewer
from mediatagger.window import Window


def test_showing_a_folders_grid_records_that_folder_and_its_drives_mount_point_in_the_state_file_under_the_config_home(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    config_home = tmp_path / "config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    stack = window.findChild(QStackedWidget)

    qtbot.keyClick(stack.currentWidget(), Qt.Key.Key_Escape)

    state = json.loads((config_home / "mediatagger" / "state.json").read_text())
    assert state == {"folder": str(folder), "mount_point": str(drive)}


def test_every_test_runs_with_the_config_home_pointing_at_a_throwaway_folder_outside_the_real_home():
    config_home = Path(os.environ["XDG_CONFIG_HOME"])

    assert (config_home.is_dir(), config_home.is_relative_to(Path.home())) == (True, False)


def test_showing_a_folders_slideshow_records_that_folder_in_the_state_file(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    config_home = tmp_path / "config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)

    state = json.loads((config_home / "mediatagger" / "state.json").read_text())
    assert state["folder"] == str(folder)


def test_with_the_config_home_unset_the_state_is_recorded_under_the_dot_config_folder_of_the_injected_home(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    home = tmp_path / "home"
    monkeypatch.delenv("XDG_CONFIG_HOME")
    monkeypatch.setenv("HOME", str(tmp_path / "environment-home"))

    window = Window(folder, player_options=SILENT, home=home, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)

    state = json.loads((home / ".config" / "mediatagger" / "state.json").read_text())
    assert state["folder"] == str(folder)


def test_the_state_file_is_not_written_when_it_would_land_on_the_apps_own_drive(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    app_drive = tmp_path / "APP"
    config_home = app_drive / "config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    window = Window(folder, player_options=SILENT, app_location=app_drive / "app" / "mediatagger", is_mount_point=lambda path: path in (drive, app_drive),
                    ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)

    assert not (config_home / "mediatagger" / "state.json").exists()


def test_the_state_file_is_written_when_the_app_and_the_config_home_both_live_on_the_system_disk(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    config_home = tmp_path / "home" / ".config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    window = Window(folder, player_options=SILENT, app_location=tmp_path / "app" / "mediatagger", is_mount_point=lambda path: path in (drive, Path("/")),
                    ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)

    assert json.loads((config_home / "mediatagger" / "state.json").read_text())["folder"] == str(folder)


def test_the_state_file_is_not_written_when_it_would_land_on_the_drive_being_viewed(qtbot, tmp_path, monkeypatch):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    config_home = drive / "config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    window = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)

    assert not (config_home / "mediatagger" / "state.json").exists()


def test_launching_the_window_with_no_path_when_the_remembered_folder_exists_opens_that_folders_grid(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    earlier = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(earlier)
    earlier.close()

    window = Window(player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)

    shown = window.findChild(QStackedWidget).currentWidget()
    assert isinstance(shown, Grid)
    assert shown.folder == folder


def test_launching_the_window_with_no_path_into_a_remembered_folders_grid_opens_that_drives_library(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    earlier = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(earlier)
    earlier.close()
    window = Window(player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)
    grid = window.findChild(QStackedWidget).currentWidget()

    grid.setCurrentIndex(grid.model().index(0, 0))

    assert "beach family" in shown_status_bar_texts(window)


def test_launching_the_window_with_no_path_into_a_remembered_folders_grid_puts_the_cursor_on_its_first_entry_and_shows_tag_badges_from_that_drives_library(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    earlier = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(earlier)
    earlier.close()

    window = Window(player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)

    grid = window.findChild(QStackedWidget).currentWidget()
    assert grid.currentIndex().row() == 0
    assert f"{TAG_BADGE}2" in painted_texts(grid, 0)


def test_launching_the_window_with_no_path_when_the_remembered_folder_no_longer_exists_shows_the_launch_screen(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    earlier = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(earlier)
    earlier.close()
    shutil.rmtree(folder)

    window = Window(player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)

    shown = window.findChild(QStackedWidget).currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow is None


def test_launching_the_window_with_no_path_and_no_state_file_shows_the_launch_screen(qtbot):
    assert not (Path(os.environ["XDG_CONFIG_HOME"]) / "mediatagger" / "state.json").exists()

    window = Window(player_options=SILENT)
    qtbot.addWidget(window)

    shown = window.findChild(QStackedWidget).currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow is None


def test_with_no_remembered_geometry_the_window_opens_not_fullscreen_at_about_80_percent_of_the_available_screen_centred(qtbot):
    available = QGuiApplication.primaryScreen().availableGeometry()

    window = Window(player_options=SILENT, is_mount_point=lambda path: False)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    frame = window.geometry()
    off_centre = (frame.center() - available.center()).manhattanLength()
    assert (window.isFullScreen(), round(frame.width() / available.width(), 2), round(frame.height() / available.height(), 2),
        off_centre <= 2) == (False, 0.8, 0.8, True)


def test_with_a_geometry_remembered_in_the_state_file_the_window_opens_at_that_size_and_position(qtbot):
    available = QGuiApplication.primaryScreen().availableGeometry()
    remembered = QRect(available.left() + 30, available.top() + 40, available.width() // 2, available.height() // 3)
    write_state_file(json.dumps({"geometry": {"x": remembered.x(), "y": remembered.y(), "width": remembered.width(), "height": remembered.height()}}))

    window = Window(player_options=SILENT, is_mount_point=lambda path: False)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    assert (window.isFullScreen(), window.geometry()) == (False, remembered)


def write_state_file(text):
    state_file = Path(os.environ["XDG_CONFIG_HOME"]) / "mediatagger" / "state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(text)
    return state_file


@pytest.mark.parametrize("state, mode", [
    pytest.param(lambda folder: "{not json", 0o644, id="unreadable state file"),
    pytest.param(lambda folder: json.dumps({"mount_point": str(folder)}), 0o644, id="state file with no folder entry"),
    pytest.param(lambda folder: json.dumps({"folder": str(folder), "mount_point": str(folder)}), 0o000, id="state file it has no permission to read"),
])
def test_launching_the_window_with_no_path_and_a_state_file_it_cannot_use_shows_the_launch_screen(qtbot, tmp_path, state, mode):
    write_state_file(state(tmp_path)).chmod(mode)

    window = Window(player_options=SILENT)
    qtbot.addWidget(window)

    shown = window.findChild(QStackedWidget).currentWidget()
    assert isinstance(shown, Viewer)
    assert shown.slideshow is None


def test_launching_the_window_with_no_path_and_no_state_file_then_closing_it_leaves_no_state_file(qtbot):
    state_file = Path(os.environ["XDG_CONFIG_HOME"]) / "mediatagger" / "state.json"

    window = Window(player_options=SILENT, is_mount_point=lambda path: False)
    qtbot.addWidget(window)
    window.close()

    assert not state_file.exists()


def test_launching_the_window_on_a_file_path_records_that_files_folder_in_the_state_file_not_the_file(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)

    window = Window(folder / "IMG_1.png", player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)

    state = json.loads((Path(os.environ["XDG_CONFIG_HOME"]) / "mediatagger" / "state.json").read_text())
    assert state["folder"] == str(folder)


def test_dropping_a_folder_onto_the_windows_launch_screen_records_that_folder_in_the_state_file(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    window = Window(player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)

    drag_and_drop_onto(window.findChild(QStackedWidget).currentWidget(), folder)

    state = json.loads((Path(os.environ["XDG_CONFIG_HOME"]) / "mediatagger" / "state.json").read_text())
    assert state["folder"] == str(folder)


def test_launching_the_window_with_no_path_into_a_remembered_folder_whose_first_item_is_tagged_beach_family_shows_beach_family_in_the_status_bar_before_any_cursor_move(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    earlier = Window(folder, player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(earlier)
    earlier.close()

    window = Window(player_options=SILENT, is_mount_point=lambda path: path == drive, ask_to_create_library=lambda question: False)
    qtbot.addWidget(window)
    show_exposed(qtbot, window)

    assert "beach family" in shown_status_bar_texts(window)
