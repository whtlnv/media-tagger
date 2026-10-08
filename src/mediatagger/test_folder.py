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
