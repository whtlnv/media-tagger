from mediatagger.fit import fit_to_screen


def test_an_image_wider_than_the_screen_is_scaled_to_the_screen_width():
    assert fit_to_screen(image=(4000, 1000), screen=(1920, 1080)) == (1920, 480)
