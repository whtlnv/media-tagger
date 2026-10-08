from mediatagger.folder import media_files


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
