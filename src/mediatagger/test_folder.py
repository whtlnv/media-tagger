from mediatagger.folder import media_files


def test_opening_a_folder_lists_its_images_in_natural_filename_order(tmp_path):
    for name in ["IMG_10.jpg", "IMG_2.jpg", "IMG_1.jpg"]:
        (tmp_path / name).touch()

    assert media_files(tmp_path) == [
        tmp_path / "IMG_1.jpg",
        tmp_path / "IMG_2.jpg",
        tmp_path / "IMG_10.jpg",
    ]
