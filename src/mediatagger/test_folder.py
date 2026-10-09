from mediatagger.folder import is_video, media_files


def test_opening_a_folder_lists_its_images_in_natural_filename_order(tmp_path):
    for name in ["IMG_10.jpg", "IMG_2.jpg", "IMG_1.jpg"]:
        (tmp_path / name).touch()

    assert media_files(tmp_path) == [
        tmp_path / "IMG_1.jpg",
        tmp_path / "IMG_2.jpg",
        tmp_path / "IMG_10.jpg",
    ]


def test_opening_a_folder_lists_its_videos_alongside_its_images_in_natural_order(tmp_path):
    for name in ["clip_10.mp4", "IMG_3.jpg", "clip_2.mov", "anim_1.gif", "IMG_20.jpg", "old_5.avi", "old_7.mpg"]:
        (tmp_path / name).touch()

    assert media_files(tmp_path) == [
        tmp_path / "IMG_3.jpg",
        tmp_path / "IMG_20.jpg",
        tmp_path / "anim_1.gif",
        tmp_path / "clip_2.mov",
        tmp_path / "clip_10.mp4",
        tmp_path / "old_5.avi",
        tmp_path / "old_7.mpg",
    ]


def test_a_non_media_file_in_the_folder_is_not_in_the_slideshow(tmp_path):
    for name in ["IMG_1.jpg", "notes.txt", "clip_2.mp4"]:
        (tmp_path / name).touch()

    assert media_files(tmp_path) == [
        tmp_path / "IMG_1.jpg",
        tmp_path / "clip_2.mp4",
    ]


def test_media_extensions_are_matched_regardless_of_case(tmp_path):
    for name in ["IMG_1.JPG", "clip_2.Mp4"]:
        (tmp_path / name).touch()

    assert media_files(tmp_path) == [
        tmp_path / "IMG_1.JPG",
        tmp_path / "clip_2.Mp4",
    ]


def test_a_hidden_file_with_a_media_extension_is_not_in_the_slideshow(tmp_path):
    for name in ["IMG_1.jpg", ".hidden.jpg"]:
        (tmp_path / name).touch()

    assert media_files(tmp_path) == [tmp_path / "IMG_1.jpg"]


def test_macos_litter_is_not_in_the_slideshow(tmp_path):
    for name in ["IMG_1.jpg", "._IMG_1.jpg", ".DS_Store"]:
        (tmp_path / name).touch()

    assert media_files(tmp_path) == [tmp_path / "IMG_1.jpg"]


def test_a_subfolder_and_the_media_inside_it_are_not_in_the_slideshow(tmp_path):
    (tmp_path / "IMG_1.jpg").touch()
    subfolder = tmp_path / "holiday.jpg"
    subfolder.mkdir()
    (subfolder / "IMG_9.jpg").touch()

    assert media_files(tmp_path) == [tmp_path / "IMG_1.jpg"]


def test_every_image_and_video_extension_in_the_design_is_in_the_slideshow(tmp_path):
    extensions = ["jpg", "jpeg", "png", "webp", "bmp", "tif", "tiff", "heic",
                  "mp4", "mov", "avi", "mpg", "mpeg", "mkv", "m4v", "wmv", "3gp", "gif"]
    names = [f"item_{i}.{ext}" for i, ext in enumerate(extensions, start=1)]
    for name in names:
        (tmp_path / name).touch()

    assert media_files(tmp_path) == [tmp_path / name for name in names]


def test_a_gif_item_is_played_as_a_video_not_shown_as_a_still_image(tmp_path):
    assert is_video(tmp_path / "dance.gif")


def test_a_still_image_is_shown_as_an_image_while_mp4_avi_mpg_are_played_as_video(tmp_path):
    names = ["IMG_1.jpg", "IMG_2.png", "IMG_3.heic", "clip_4.mp4", "old_5.avi", "old_6.mpg"]

    assert {name: is_video(tmp_path / name) for name in names} == {
        "IMG_1.jpg": False,
        "IMG_2.png": False,
        "IMG_3.heic": False,
        "clip_4.mp4": True,
        "old_5.avi": True,
        "old_6.mpg": True,
    }


def test_every_video_extension_design_md_lists_is_played_as_video_regardless_of_case(tmp_path):
    names = ["a.mp4", "b.MOV", "c.avi", "d.mpg", "e.MPEG", "f.mkv", "g.m4v", "h.wmv", "i.3gp", "j.GIF", "k.MP4"]
    assert [name for name in names if not is_video(tmp_path / name)] == []
