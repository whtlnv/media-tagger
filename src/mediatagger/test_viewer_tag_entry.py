import pytest
from PySide6.QtCore import QPoint, Qt

from mediatagger.library import Library
from mediatagger.test_video import wait_until_playing
from mediatagger.test_viewer import make_image, make_surface_ready, shown_labels, shown_texts, shows_video_surface
from mediatagger.test_viewer_library import (
    drive_with_a_tag_library_holding_one_clip, drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, frame_in, make_tag_library_drive, resize_and_wait,
    shown_viewer_on_drive, shown_viewer_on_drives, visible_tag_prompt_texts, visible_tag_prompts,
)
from mediatagger.test_viewer_open import drag_and_drop_onto, make_folders


def test_pressing_t_in_the_viewer_on_a_file_with_no_tags_opens_the_tag_prompt_showing_no_tags(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert visible_tag_prompt_texts(viewer) == [""]


def test_pressing_t_on_a_file_tagged_beach_family_shows_beach_family_as_text_beside_the_tag_prompts_empty_input(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "family beach")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert visible_tag_prompt_texts(viewer) == [""]
    assert "beach family" in shown_texts(viewer)


def test_typing_beach_family_in_the_tag_prompt_and_pressing_enter_closes_it_and_records_both_tags_in_the_drives_tags_db(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    enter_in_tag_prompt(qtbot, viewer, "beach family")

    assert visible_tag_prompt_texts(viewer) == []
    assert Library.open(drive).tags(folder / "IMG_1.png") == ["beach", "family"]


def test_on_a_file_tagged_beach_family_typing_minus_family_in_the_tag_prompt_and_pressing_enter_leaves_it_tagged_only_beach(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    enter_in_tag_prompt(qtbot, viewer, "-family")

    assert Library.open(drive).tags(folder / "IMG_1.png") == ["beach"]


def test_pressing_t_again_after_closing_the_tag_prompt_shows_only_one_tag_prompt_with_one_copy_of_the_files_tags(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    enter_in_tag_prompt(qtbot, viewer, "beach")

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    assert visible_tag_prompt_texts(viewer) == [""]
    assert shown_texts(viewer).count("beach family") == 1


def test_the_tag_prompt_is_drawn_inside_the_viewer_window_centred_horizontally_near_the_bottom_just_above_the_status_bar(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    resize_and_wait(qtbot, viewer, 1600, 900)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    [prompt] = visible_tag_prompts(viewer)
    frame = frame_in(viewer, prompt)
    assert prompt.window() is viewer
    assert abs(frame.center().x() - viewer.rect().center().x()) <= 1
    assert viewer.height() * 3 // 4 <= frame.bottom() < viewer.status_bar.geometry().top()


def test_after_the_window_is_resized_while_the_tag_prompt_is_open_the_prompt_is_still_centred_just_above_the_status_bar(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    resize_and_wait(qtbot, viewer, 1600, 900)
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    resize_and_wait(qtbot, viewer, 1000, 700)

    [prompt] = visible_tag_prompts(viewer)
    frame = frame_in(viewer, prompt)
    assert abs(frame.center().x() - viewer.rect().center().x()) <= 1
    assert viewer.height() * 3 // 4 <= frame.bottom() < viewer.status_bar.geometry().top()


def test_pressing_t_makes_the_tag_prompts_input_the_viewers_focus_widget(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    [prompt] = visible_tag_prompts(viewer)
    assert viewer.focusWidget() is prompt


def test_the_tag_prompts_shown_tags_are_styled_like_the_info_overlay(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    [tags] = [label for label in shown_labels(viewer) if label.text() == "beach family"]
    assert tags.styleSheet() == viewer.info.styleSheet()


def test_the_tag_prompts_input_reads_as_a_text_box_with_a_light_border_and_a_lighter_background_than_its_shown_tags(qtbot, tmp_path):
    drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    [folder] = make_folders(drive, "Photos")
    make_image(folder / "IMG_1.png", "black")
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    [prompt] = visible_tag_prompts(viewer)
    [tags] = [label for label in shown_labels(viewer) if label.text() == "beach family"]
    frame = viewer.grab().toImage()
    ratio = frame.devicePixelRatio()
    def colour_at(widget, x, y):
        point = widget.mapTo(viewer, QPoint(x, y))
        return frame.pixelColor(int(point.x() * ratio), int(point.y() * ratio))
    border = colour_at(prompt, prompt.width() // 2, 0)
    input_background = colour_at(prompt, prompt.width() - 4, prompt.height() // 2)
    tags_background = colour_at(tags, tags.width() - 4, tags.height() // 2)
    assert border.lightness() > 150
    assert input_background.lightness() > tags_background.lightness()


def test_typing_space_i_p_f_m_in_the_open_tag_prompt_goes_into_it_and_leaves_the_slideshow_and_info_overlay_unchanged(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_T)
    window_state = viewer.windowState()

    qtbot.keyClicks(viewer.focusWidget(), " ipfm")

    assert visible_tag_prompt_texts(viewer) == [" ipfm"]
    assert viewer.slideshow.current == folder / "IMG_1.png"
    assert not viewer.info.isVisible()
    assert viewer.windowState() == window_state


def test_typing_p_and_m_in_the_tag_prompt_open_over_a_playing_video_neither_pauses_nor_mutes_it(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=30)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    wait_until_playing(engine)
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    qtbot.keyClicks(viewer.focusWidget(), "pm")

    assert visible_tag_prompt_texts(viewer) == ["pm"]
    assert [engine.pause, engine.mute] == [False, False]


def test_pressing_enter_in_the_tag_prompt_over_a_playing_video_saves_the_tags_without_pausing_it(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=30)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    wait_until_playing(engine)

    enter_in_tag_prompt(qtbot, viewer, "beach")

    assert Library.open(drive).tags(folder / "IMG_1.mp4") == ["beach"]
    assert engine.pause is False


def test_arrow_keys_in_the_tag_prompt_open_over_a_paused_video_neither_move_the_slideshow_nor_seek_it(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path, duration=60)
    make_image(folder / "IMG_2.png", "red")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    make_surface_ready(viewer)
    engine = viewer.video_player.engine
    wait_until_playing(engine)
    qtbot.keyClick(viewer, Qt.Key.Key_P)
    engine.time_pos = 20
    engine.wait_for_property("time-pos", lambda time_pos: time_pos == pytest.approx(20, abs=1), timeout=5)
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    for key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
        qtbot.keyClick(viewer.focusWidget(), key)
        qtbot.wait(300)  # mpv seeks asynchronously, so give a stray seek time to land

        assert viewer.slideshow.current == folder / "IMG_1.mp4"
        assert engine.time_pos == pytest.approx(20, abs=1)


def test_pressing_esc_in_the_tag_prompt_closes_it_leaving_the_viewer_open_and_the_files_tags_unchanged(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_T)
    qtbot.keyClicks(viewer.focusWidget(), "-family sunset")

    qtbot.keyClick(viewer.focusWidget(), Qt.Key.Key_Escape)

    assert visible_tag_prompt_texts(viewer) == []
    assert Library.open(drive).tags(folder / "IMG_1.png") == ["beach", "family"]
    assert viewer.isVisible()


def test_pressing_esc_after_esc_has_closed_the_tag_prompt_closes_the_viewer(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_T)
    qtbot.keyClick(viewer.focusWidget(), Qt.Key.Key_Escape)

    qtbot.keyClick(viewer, Qt.Key.Key_Escape)

    assert not viewer.isVisible()


def test_pressing_esc_in_the_tag_prompt_also_hides_its_shown_tags(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    qtbot.keyClick(viewer.focusWidget(), Qt.Key.Key_Escape)

    assert visible_tag_prompts(viewer) == []
    assert not viewer.prompt_tags.isVisible()


def test_pressing_t_on_a_video_shows_the_tag_prompt_and_its_shown_tags_above_the_video_surface(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_clip(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.mp4", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.waitUntil(lambda: shows_video_surface(viewer))

    qtbot.keyClick(viewer, Qt.Key.Key_T)

    [prompt] = visible_tag_prompts(viewer)
    [tags] = [label for label in shown_labels(viewer) if label.text() == "beach family"]
    assert viewer.childAt(prompt.geometry().center()) is prompt
    assert viewer.childAt(tags.geometry().center()) is tags


def test_after_dropping_a_folder_from_a_second_drive_with_a_tag_library_tags_entered_in_the_prompt_are_recorded_in_the_second_drives_tags_db_not_the_firsts(qtbot, tmp_path):
    first_drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    second_drive = make_tag_library_drive(tmp_path / "BACKUP")
    [viewed] = make_folders(first_drive, "Photos")
    [dropped] = make_folders(second_drive, "Photos")
    make_image(viewed / "IMG_1.png", "red")
    make_image(dropped / "IMG_1.png", "green")
    viewer = shown_viewer_on_drives(qtbot, viewed, (first_drive, second_drive), lambda question: False)
    drag_and_drop_onto(viewer, dropped)

    enter_in_tag_prompt(qtbot, viewer, "beach family")

    assert Library.open(second_drive).tags(dropped / "IMG_1.png") == ["beach", "family"]
    assert Library.open(first_drive).tags(viewed / "IMG_1.png") == []


def test_dropping_a_folder_while_the_tag_prompt_is_open_closes_it_without_saving_what_was_typed(qtbot, tmp_path):
    first_drive = make_tag_library_drive(tmp_path / "MEDIATAGGER")
    second_drive = make_tag_library_drive(tmp_path / "BACKUP")
    [viewed] = make_folders(first_drive, "Photos")
    [dropped] = make_folders(second_drive, "Photos")
    make_image(viewed / "IMG_1.png", "red")
    make_image(dropped / "IMG_1.png", "green")
    viewer = shown_viewer_on_drives(qtbot, viewed, (first_drive, second_drive), lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_T)
    [prompt] = visible_tag_prompts(viewer)
    qtbot.keyClicks(prompt, "beach")

    drag_and_drop_onto(viewer, dropped)

    assert visible_tag_prompt_texts(viewer) == []
    assert Library.open(first_drive).tags(viewed / "IMG_1.png") == []
