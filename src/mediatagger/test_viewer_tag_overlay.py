import shutil

from PySide6.QtCore import Qt

from mediatagger.library import Library
from mediatagger.test_video import make_clip
from mediatagger.test_viewer import make_image, shown_labels, shown_texts, shows_video_surface
from mediatagger.test_viewer_library import (
    drive_with_a_tag_library_holding_one_image, enter_in_tag_prompt, frame_in, made_read_only, resize_and_wait, shown_viewer_on_drive, visible_tag_prompts,
)
from mediatagger.test_viewer_open import make_folders
from mediatagger.status_bar import CORNER_MARGIN


def test_after_entering_beach_family_in_the_tag_prompt_a_tag_overlay_shows_beach_family_while_the_prompt_is_closed(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    enter_in_tag_prompt(qtbot, viewer, "beach family")

    assert visible_tag_prompts(viewer) == []
    assert shown_texts(viewer) == ["beach family"]


def test_after_esc_closes_the_tag_prompt_on_a_file_tagged_beach_family_the_tag_overlay_shows_beach_family_again(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    qtbot.keyClick(viewer.focusWidget(), Qt.Key.Key_Escape)

    assert visible_tag_prompts(viewer) == []
    assert shown_texts(viewer) == ["beach family"]


def test_after_esc_closes_the_tag_prompt_on_a_file_with_no_tags_the_tag_overlay_is_hidden(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_T)

    qtbot.keyClick(viewer.focusWidget(), Qt.Key.Key_Escape)

    assert visible_tag_prompts(viewer) == []
    assert shown_texts(viewer) == []


def test_moving_with_space_from_a_file_tagged_beach_family_to_an_untagged_one_hides_the_tag_overlay_and_left_back_shows_beach_family_again(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    enter_in_tag_prompt(qtbot, viewer, "beach family")

    qtbot.keyClick(viewer, Qt.Key.Key_Space)
    assert shown_texts(viewer) == []

    qtbot.keyClick(viewer, Qt.Key.Key_Left)
    assert shown_texts(viewer) == ["beach family"]


def test_opening_a_folder_whose_first_file_was_tagged_beach_family_in_an_earlier_viewer_shows_beach_family_in_the_tag_overlay(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    earlier = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    enter_in_tag_prompt(qtbot, earlier, "beach family")
    earlier.close()

    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    assert shown_texts(viewer) == ["beach family"]


def test_the_tag_overlay_sits_in_the_top_right_corner_a_corner_margin_from_the_top_and_right_edges(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    resize_and_wait(qtbot, viewer, 1600, 900)

    [tag_overlay] = shown_labels(viewer)
    frame = frame_in(viewer, tag_overlay)
    assert frame.top() == CORNER_MARGIN
    assert frame.right() == viewer.rect().right() - CORNER_MARGIN


def test_after_space_to_a_file_with_longer_tags_the_tag_overlay_still_ends_a_corner_margin_from_the_right_edge(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_image(folder / "IMG_2.png", "blue")
    library = Library.open(drive)
    library.enter(folder / "IMG_1.png", "beach")
    library.enter(folder / "IMG_2.png", "beach family holiday grandparents sunset")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    resize_and_wait(qtbot, viewer, 1600, 900)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)

    [tag_overlay] = shown_labels(viewer)
    frame = frame_in(viewer, tag_overlay)
    assert frame.right() == viewer.rect().right() - CORNER_MARGIN


def test_the_tag_overlay_has_the_same_look_as_the_info_overlay(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    [tag_overlay] = shown_labels(viewer)
    assert tag_overlay.text() == "beach family"
    assert tag_overlay.styleSheet() == viewer.info.styleSheet()


def test_after_the_window_is_resized_the_tag_overlay_is_still_a_corner_margin_from_the_top_and_right_edges(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    resize_and_wait(qtbot, viewer, 1600, 900)

    resize_and_wait(qtbot, viewer, 1000, 700)

    [tag_overlay] = shown_labels(viewer)
    frame = frame_in(viewer, tag_overlay)
    assert frame.top() == CORNER_MARGIN
    assert frame.right() == viewer.rect().right() - CORNER_MARGIN


def test_with_the_info_overlay_and_the_read_only_banner_showing_the_tag_overlay_overlaps_neither(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder / "IMG_1.png", "beach family")
    with made_read_only(drive):
        viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    qtbot.keyClick(viewer, Qt.Key.Key_I)

    [tag_overlay] = [label for label in shown_labels(viewer) if label.text() == "beach family"]
    assert viewer.info.isVisible() and viewer.read_only_banner.isVisible()
    assert not frame_in(viewer, tag_overlay).intersects(frame_in(viewer, viewer.info))
    assert not frame_in(viewer, tag_overlay).intersects(frame_in(viewer, viewer.read_only_banner))


def test_moving_with_space_from_an_image_to_a_video_tagged_beach_family_shows_the_tag_overlay_on_top_of_the_video(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    make_clip(folder / "IMG_2.mp4")
    Library.open(drive).enter(folder / "IMG_2.mp4", "beach family")
    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    qtbot.keyClick(viewer, Qt.Key.Key_Space)
    qtbot.waitUntil(lambda: shows_video_surface(viewer))

    [tag_overlay] = [label for label in shown_labels(viewer) if label.text() == "beach family"]
    assert viewer.childAt(tag_overlay.geometry().center()) is tag_overlay


def test_a_file_tagged_beach_family_in_a_viewer_shows_beach_family_in_the_tag_overlay_of_a_viewer_on_a_copy_of_the_drive_at_another_root(qtbot, tmp_path):
    original_drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    [other_drive] = make_folders(tmp_path, "ELSEWHERE")
    earlier = shown_viewer_on_drive(qtbot, folder, original_drive, lambda question: False)
    enter_in_tag_prompt(qtbot, earlier, "beach family")
    earlier.close()
    shutil.copytree(original_drive, other_drive, dirs_exist_ok=True)

    viewer = shown_viewer_on_drive(qtbot, other_drive / "Photos", other_drive, lambda question: False)

    assert shown_texts(viewer) == ["beach family"]


def test_the_tag_overlay_shows_the_files_own_tags_alphabetically_then_its_inherited_tags_alphabetically(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    trip = folder / "Trip"
    trip.mkdir()
    make_image(trip / "IMG_1.png", "red")
    library = Library.open(drive)
    library.enter(folder, "aunt")
    library.enter(trip, "zoo")
    library.enter(trip / "IMG_1.png", "sunset beach")

    viewer = shown_viewer_on_drive(qtbot, trip, drive, lambda question: False)

    assert " ".join(shown_texts(viewer)) == "beach sunset aunt zoo"


def test_in_the_tag_overlay_an_inherited_tag_is_drawn_dimmer_than_an_own_tag(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    library = Library.open(drive)
    library.enter(folder, "aunt")
    library.enter(folder / "IMG_1.png", "beach")

    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)

    frames = [frame_in(viewer, label) for label in shown_labels(viewer) if "beach" in label.text() or "aunt" in label.text()]
    left = min(frame.left() for frame in frames)
    right = max(frame.right() for frame in frames)
    top = min(frame.top() for frame in frames)
    bottom = max(frame.bottom() for frame in frames)
    image = viewer.grab().toImage()

    def brightest_in(columns):
        return max(image.pixelColor(x, y).lightness() for x in columns for y in range(top, bottom + 1))
    width = right - left
    own_brightness = brightest_in(range(left, left + width // 4))  # "beach", shown first
    inherited_brightness = brightest_in(range(right - width // 3, right))  # "aunt", shown last
    assert own_brightness > 240
    assert inherited_brightness < own_brightness - 60


def test_a_file_with_no_own_tags_in_a_folder_tagged_aunt_shows_aunt_in_the_tag_overlay_in_the_top_right_corner(qtbot, tmp_path):
    drive, folder = drive_with_a_tag_library_holding_one_image(tmp_path)
    Library.open(drive).enter(folder, "aunt")

    viewer = shown_viewer_on_drive(qtbot, folder, drive, lambda question: False)
    resize_and_wait(qtbot, viewer, 1600, 900)

    [tag_overlay] = shown_labels(viewer)
    assert tag_overlay.text() == "aunt"
    frame = frame_in(viewer, tag_overlay)
    assert frame.top() == CORNER_MARGIN
    assert frame.right() == viewer.rect().right() - CORNER_MARGIN
