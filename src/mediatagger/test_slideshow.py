from mediatagger.slideshow import Slideshow


def touch(folder, *names):
    for name in names:
        (folder / name).touch()


def test_opening_a_folder_path_shows_its_first_item(tmp_path):
    touch(tmp_path, "IMG_10.jpg", "IMG_2.jpg", "notes.txt")

    assert Slideshow.open(tmp_path).current == tmp_path / "IMG_2.jpg"


def test_opening_a_file_path_shows_that_file(tmp_path):
    touch(tmp_path, "IMG_1.jpg", "IMG_2.jpg", "IMG_3.jpg")

    assert Slideshow.open(tmp_path / "IMG_2.jpg").current == tmp_path / "IMG_2.jpg"


def test_pressing_space_shows_the_next_item(tmp_path):
    touch(tmp_path, "IMG_1.jpg", "IMG_2.jpg", "IMG_3.jpg")
    slideshow = Slideshow.open(tmp_path)

    slideshow.press("Space")

    assert slideshow.current == tmp_path / "IMG_2.jpg"


def test_pressing_right_arrow_shows_the_next_item(tmp_path):
    touch(tmp_path, "IMG_1.jpg", "IMG_2.jpg", "IMG_3.jpg")
    slideshow = Slideshow.open(tmp_path)

    slideshow.press("Right")

    assert slideshow.current == tmp_path / "IMG_2.jpg"


def test_pressing_left_arrow_shows_the_previous_item(tmp_path):
    touch(tmp_path, "IMG_1.jpg", "IMG_2.jpg", "IMG_3.jpg")
    slideshow = Slideshow.open(tmp_path / "IMG_2.jpg")

    slideshow.press("Left")

    assert slideshow.current == tmp_path / "IMG_1.jpg"
