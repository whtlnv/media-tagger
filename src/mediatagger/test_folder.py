import pytest

from mediatagger.folder import is_video, media_files


def touch(folder, *names):
    for name in names:
        (folder / name).touch()


EXTENSIONS_IN_THE_DESIGN = ["jpg", "jpeg", "png", "webp", "bmp", "tif", "tiff", "heic",
                            "mp4", "mov", "avi", "mpg", "mpeg", "mkv", "m4v", "wmv", "3gp", "gif"]
ONE_ITEM_PER_EXTENSION = [f"item_{i}.{ext}" for i, ext in enumerate(EXTENSIONS_IN_THE_DESIGN, start=1)]


@pytest.mark.parametrize("names, listed", [
    pytest.param(["IMG_10.jpg", "IMG_2.jpg", "IMG_1.jpg"], ["IMG_1.jpg", "IMG_2.jpg", "IMG_10.jpg"],
                 id="images in natural filename order"),
    pytest.param(["clip_10.mp4", "IMG_3.jpg", "clip_2.mov", "anim_1.gif", "IMG_20.jpg", "old_5.avi", "old_7.mpg"],
                 ["anim_1.gif", "clip_2.mov", "clip_10.mp4", "IMG_3.jpg", "IMG_20.jpg", "old_5.avi", "old_7.mpg"],
                 id="videos alongside images in natural order"),
    pytest.param(["IMG_1.JPG", "clip_2.Mp4"], ["clip_2.Mp4", "IMG_1.JPG"],
                 id="extensions matched regardless of case"),
    pytest.param(ONE_ITEM_PER_EXTENSION, ONE_ITEM_PER_EXTENSION, id="every image and video extension in the design"),
])
def test_opening_a_folder_lists_its_media_in_natural_filename_order(tmp_path, names, listed):
    touch(tmp_path, *names)

    assert media_files(tmp_path) == [tmp_path / name for name in listed]


@pytest.mark.parametrize("names, listed", [
    pytest.param(["IMG_1.jpg", "notes.txt", "clip_2.mp4"], ["clip_2.mp4", "IMG_1.jpg"], id="non-media file"),
    pytest.param(["IMG_1.jpg", ".hidden.jpg"], ["IMG_1.jpg"], id="hidden file with a media extension"),
    pytest.param(["IMG_1.jpg", "._IMG_1.jpg", ".DS_Store"], ["IMG_1.jpg"], id="macOS litter"),
])
def test_a_file_that_is_not_shown_media_is_not_in_the_slideshow(tmp_path, names, listed):
    touch(tmp_path, *names)

    assert media_files(tmp_path) == [tmp_path / name for name in listed]


def test_a_subfolder_and_the_media_inside_it_are_not_in_the_slideshow(tmp_path):
    (tmp_path / "IMG_1.jpg").touch()
    subfolder = tmp_path / "holiday.jpg"
    subfolder.mkdir()
    (subfolder / "IMG_9.jpg").touch()

    assert media_files(tmp_path) == [tmp_path / "IMG_1.jpg"]


@pytest.mark.parametrize("name, played_as_video", [
    ("dance.gif", True),
    ("IMG_1.jpg", False), ("IMG_2.png", False), ("IMG_3.heic", False),
    ("clip_4.mp4", True), ("old_5.avi", True), ("old_6.mpg", True),
    ("a.mp4", True), ("b.MOV", True), ("c.avi", True), ("d.mpg", True), ("e.MPEG", True), ("f.mkv", True),
    ("g.m4v", True), ("h.wmv", True), ("i.3gp", True), ("j.GIF", True), ("k.MP4", True),
])
def test_a_still_image_is_shown_as_an_image_while_every_video_extension_and_gif_is_played_as_video_in_any_case(
        tmp_path, name, played_as_video):
    assert is_video(tmp_path / name) is played_as_video


def test_natural_order_ignores_letter_case(tmp_path):
    names = ["CLIP_0003.AVI", "IMG_0001.jpg", "img_0002_tall.jpg", "IMG_0004.mp4", "broken_0005.jpg"]
    touch(tmp_path, *names)

    assert [path.name for path in media_files(tmp_path)] == [
        "broken_0005.jpg", "CLIP_0003.AVI", "IMG_0001.jpg", "img_0002_tall.jpg", "IMG_0004.mp4",
    ]
