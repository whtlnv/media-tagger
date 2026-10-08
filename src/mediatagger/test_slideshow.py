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


def test_stepping_from_an_opened_file_moves_relative_to_that_file(tmp_path):
    touch(tmp_path, "IMG_1.jpg", "IMG_2.jpg", "IMG_3.jpg")
    slideshow = Slideshow.open(tmp_path / "IMG_2.jpg")

    slideshow.press("Space")
    assert slideshow.current == tmp_path / "IMG_3.jpg"

    slideshow.press("Left")
    slideshow.press("Left")
    assert slideshow.current == tmp_path / "IMG_1.jpg"


def test_stepping_forward_on_the_last_item_keeps_showing_it(tmp_path):
    touch(tmp_path, "IMG_1.jpg", "IMG_2.jpg", "IMG_3.jpg")
    slideshow = Slideshow.open(tmp_path / "IMG_3.jpg")

    slideshow.press("Space")
    assert slideshow.current == tmp_path / "IMG_3.jpg"

    slideshow.press("Right")
    assert slideshow.current == tmp_path / "IMG_3.jpg"


def test_stepping_back_on_the_first_item_keeps_showing_it(tmp_path):
    touch(tmp_path, "IMG_1.jpg", "IMG_2.jpg", "IMG_3.jpg")
    slideshow = Slideshow.open(tmp_path)

    slideshow.press("Left")

    assert slideshow.current == tmp_path / "IMG_1.jpg"


def test_the_info_overlay_is_hidden_when_the_viewer_opens(tmp_path):
    touch(tmp_path, "IMG_1.jpg", "IMG_2.jpg", "IMG_3.jpg")

    assert Slideshow.open(tmp_path).overlay is None


def test_pressing_i_shows_an_overlay_with_the_filename_and_position(tmp_path):
    touch(tmp_path, "IMG_1.jpg", "IMG_2.jpg", "IMG_3.jpg", "IMG_4.jpg", "IMG_5.jpg")
    slideshow = Slideshow.open(tmp_path / "IMG_3.jpg")

    slideshow.press("i")

    assert "IMG_3.jpg" in slideshow.overlay
    assert "3 / 5" in slideshow.overlay


def test_the_info_overlay_updates_its_filename_and_position_when_moving_to_another_item(tmp_path):
    touch(tmp_path, "IMG_1.jpg", "IMG_2.jpg", "IMG_3.jpg", "IMG_4.jpg", "IMG_5.jpg")
    slideshow = Slideshow.open(tmp_path / "IMG_3.jpg")
    slideshow.press("i")

    slideshow.press("Right")

    assert "IMG_4.jpg" in slideshow.overlay
    assert "4 / 5" in slideshow.overlay
