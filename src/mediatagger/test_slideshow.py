from mediatagger.slideshow import Slideshow


def test_opening_a_folder_path_shows_its_first_item(tmp_path):
    for name in ["IMG_10.jpg", "IMG_2.jpg", "notes.txt"]:
        (tmp_path / name).touch()

    assert Slideshow.open(tmp_path).current == tmp_path / "IMG_2.jpg"
