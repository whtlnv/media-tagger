def fit_to_screen(image, screen):
    image_width, image_height = image
    screen_width, screen_height = screen
    image_is_wider_than_screen = image_width * screen_height > image_height * screen_width
    if image_is_wider_than_screen:
        return (screen_width, image_height * screen_width // image_width)
    return (image_width * screen_height // image_height, screen_height)
