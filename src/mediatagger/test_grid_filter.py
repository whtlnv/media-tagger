import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMenu, QWidget

from mediatagger.grid import Grid
from mediatagger.grid_filter import MISSING_TAGS, NO_TAGS, WITH_TAGS, FilterButton, GridFilter
from mediatagger.library import Library
from mediatagger.test_folder import touch


def shown_tile_names(grid):
    model = grid.model()
    return [model.index(row, 0).data(Qt.ItemDataRole.DisplayRole)
            for row in range(model.rowCount()) if not grid.isRowHidden(row)]


def test_in_a_folder_grid_sharing_the_windows_filter_with_no_filter_chosen_every_file_tile_shows(qtbot, tmp_path):
    touch(tmp_path, "a.jpg", "b.mp4", "c.jpg")
    grid = Grid(tmp_path, grid_filter=GridFilter())
    qtbot.addWidget(grid)

    assert shown_tile_names(grid) == ["a.jpg", "b.mp4", "c.jpg"]


def chosen(text):
    grid_filter = GridFilter()
    grid_filter.choose(text)
    return grid_filter


def test_with_with_tags_chosen_a_folder_grid_hides_a_file_that_has_no_own_tags(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg", "city.jpg")
    library.enter(tmp_path / "beach.jpg", "sea")
    grid = Grid(tmp_path, library=library, grid_filter=chosen(WITH_TAGS))
    qtbot.addWidget(grid)

    assert "city.jpg" not in shown_tile_names(grid)


def test_with_with_tags_chosen_a_folder_grid_keeps_showing_a_file_that_has_own_tags(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg", "city.jpg")
    library.enter(tmp_path / "beach.jpg", "sea")
    grid = Grid(tmp_path, library=library, grid_filter=chosen(WITH_TAGS))
    qtbot.addWidget(grid)

    assert shown_tile_names(grid) == ["beach.jpg"]


def test_with_with_tags_chosen_a_file_whose_only_tags_are_inherited_from_its_folder_is_hidden(qtbot, tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "trip").mkdir()
    touch(tmp_path / "trip", "beach.jpg")
    library.enter(tmp_path / "trip", "holiday")
    grid = Grid(tmp_path / "trip", library=library, grid_filter=chosen(WITH_TAGS))
    qtbot.addWidget(grid)

    assert shown_tile_names(grid) == []


def test_with_no_tags_chosen_a_folder_grid_hides_a_file_that_has_own_tags(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg", "city.jpg")
    library.enter(tmp_path / "beach.jpg", "sea")
    grid = Grid(tmp_path, library=library, grid_filter=chosen(NO_TAGS))
    qtbot.addWidget(grid)

    assert "beach.jpg" not in shown_tile_names(grid)


def test_with_no_tags_chosen_a_folder_grid_keeps_showing_a_file_with_no_own_tags_even_one_that_inherits_tags(qtbot, tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "trip").mkdir()
    touch(tmp_path / "trip", "beach.jpg", "city.jpg")
    library.enter(tmp_path / "trip", "holiday")
    library.enter(tmp_path / "trip" / "city.jpg", "street")
    grid = Grid(tmp_path / "trip", library=library, grid_filter=chosen(NO_TAGS))
    qtbot.addWidget(grid)

    assert shown_tile_names(grid) == ["beach.jpg"]


def test_with_missing_tags_chosen_a_folder_grid_hides_a_file_that_carries_no_missing_mark(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg", "city.jpg")
    library.enter(tmp_path / "beach.jpg", "type:photo")
    grid = Grid(tmp_path, library=library, required_roots=("type:",), grid_filter=chosen(MISSING_TAGS))
    qtbot.addWidget(grid)

    assert "beach.jpg" not in shown_tile_names(grid)


def test_with_missing_tags_chosen_a_folder_grid_keeps_showing_a_file_that_carries_a_missing_mark(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg", "city.jpg")
    library.enter(tmp_path / "beach.jpg", "type:photo")
    grid = Grid(tmp_path, library=library, required_roots=("type:",), grid_filter=chosen(MISSING_TAGS))
    qtbot.addWidget(grid)

    assert shown_tile_names(grid) == ["city.jpg"]


@pytest.mark.parametrize("text", [WITH_TAGS, NO_TAGS, MISSING_TAGS])
def test_under_any_filter_folder_tiles_stay_shown(qtbot, tmp_path, text):
    library = Library.create(tmp_path)
    (tmp_path / "tagged").mkdir()
    (tmp_path / "untagged").mkdir()
    library.enter(tmp_path / "tagged", "type:photo")
    grid = Grid(tmp_path, library=library, required_roots=("type:",), grid_filter=chosen(text))
    qtbot.addWidget(grid)

    assert shown_tile_names(grid) == ["tagged", "untagged"]


def grid_of_a_tagged_and_an_untagged_file(qtbot, tmp_path, grid_filter):
    library = Library.create(tmp_path)
    touch(tmp_path, "beach.jpg", "city.jpg")
    library.enter(tmp_path / "beach.jpg", "sea")
    grid = Grid(tmp_path, library=library, grid_filter=grid_filter)
    qtbot.addWidget(grid)
    return grid


def test_choosing_a_second_filter_replaces_the_first(qtbot, tmp_path):
    grid_filter = chosen(WITH_TAGS)
    grid = grid_of_a_tagged_and_an_untagged_file(qtbot, tmp_path, grid_filter)

    grid_filter.choose(NO_TAGS)

    assert shown_tile_names(grid) == ["city.jpg"]


def test_choosing_the_active_filter_again_turns_filtering_off_and_every_tile_shows_again(qtbot, tmp_path):
    grid_filter = chosen(WITH_TAGS)
    grid = grid_of_a_tagged_and_an_untagged_file(qtbot, tmp_path, grid_filter)

    grid_filter.choose(WITH_TAGS)

    assert (grid_filter.active, shown_tile_names(grid)) == (None, ["beach.jpg", "city.jpg"])


def test_choosing_a_filter_while_a_grid_is_shown_hides_its_non_matching_files_at_once(qtbot, tmp_path):
    grid_filter = GridFilter()
    grid = grid_of_a_tagged_and_an_untagged_file(qtbot, tmp_path, grid_filter)
    grid.show()

    grid_filter.choose(WITH_TAGS)

    assert shown_tile_names(grid) == ["beach.jpg"]


@pytest.mark.parametrize("text", [WITH_TAGS, NO_TAGS, MISSING_TAGS])
def test_under_any_filter_a_search_results_grid_keeps_showing_missing_result_tiles(qtbot, tmp_path, text):
    library = Library.create(tmp_path)
    touch(tmp_path, "gone.jpg")
    library.enter(tmp_path / "gone.jpg", "beach")
    (tmp_path / "gone.jpg").unlink()
    grid = Grid(tmp_path, library=library, paths=[tmp_path / "gone.jpg"], required_roots=("type:",), grid_filter=chosen(text))
    qtbot.addWidget(grid)

    assert shown_tile_names(grid) == ["gone.jpg"]


def cursor_name(grid):
    return grid.currentIndex().data(Qt.ItemDataRole.DisplayRole)


def test_choosing_a_filter_that_hides_the_cursors_tile_moves_the_cursor_to_the_next_shown_tile_after_it(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "a.jpg", "b.jpg", "c.jpg")
    library.enter(tmp_path / "a.jpg", "sea")
    library.enter(tmp_path / "c.jpg", "sea")
    grid_filter = GridFilter()
    grid = Grid(tmp_path, at=tmp_path / "b.jpg", library=library, grid_filter=grid_filter)
    qtbot.addWidget(grid)

    grid_filter.choose(WITH_TAGS)

    assert cursor_name(grid) == "c.jpg"


def test_choosing_a_filter_that_hides_the_cursors_tile_with_no_shown_tile_after_it_moves_the_cursor_to_the_nearest_shown_tile_before_it(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "a.jpg", "b.jpg", "c.jpg")
    library.enter(tmp_path / "a.jpg", "sea")
    library.enter(tmp_path / "b.jpg", "sea")
    grid_filter = GridFilter()
    grid = Grid(tmp_path, at=tmp_path / "c.jpg", library=library, grid_filter=grid_filter)
    qtbot.addWidget(grid)

    grid_filter.choose(WITH_TAGS)

    assert cursor_name(grid) == "b.jpg"


def test_choosing_a_filter_that_leaves_the_cursors_tile_shown_keeps_the_cursor_where_it_is(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "a.jpg", "b.jpg", "c.jpg")
    library.enter(tmp_path / "b.jpg", "sea")
    grid_filter = GridFilter()
    grid = Grid(tmp_path, at=tmp_path / "b.jpg", library=library, grid_filter=grid_filter)
    qtbot.addWidget(grid)

    grid_filter.choose(WITH_TAGS)

    assert cursor_name(grid) == "b.jpg"


def test_a_grid_opened_at_a_file_the_filter_hides_puts_the_cursor_on_the_next_shown_tile_after_it(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "a.jpg", "b.jpg", "c.jpg")
    library.enter(tmp_path / "a.jpg", "sea")
    library.enter(tmp_path / "c.jpg", "sea")
    grid = Grid(tmp_path, at=tmp_path / "b.jpg", library=library, grid_filter=chosen(WITH_TAGS))
    qtbot.addWidget(grid)

    assert cursor_name(grid) == "c.jpg"


def test_a_grid_under_a_filter_asks_for_its_shown_tiles_in_view_before_a_hidden_tile_among_them(qtbot, tmp_path, monkeypatch):
    import threading

    from mediatagger import grid as grid_module

    lock = threading.Lock()
    started = []

    def generate(path):
        with lock:
            started.append(path.name)
        return None, None

    monkeypatch.setattr(grid_module, "thumbnail_and_duration", generate)
    names = [f"IMG_{i:03}.jpg" for i in range(200)]
    touch(tmp_path, *names)
    library = Library.create(tmp_path)
    library.enter(tmp_path / names[1], "sea")
    grid = Grid(tmp_path, at=tmp_path / names[0], library=library, grid_filter=chosen(NO_TAGS))
    qtbot.addWidget(grid)
    grid.resize(800, 600)
    grid.show()
    qtbot.waitExposed(grid)

    qtbot.waitUntil(lambda: names[2] in started and names[1] in started)

    with lock:
        assert started.index(names[2]) < started.index(names[1])


def shown_filtered_grid(qtbot, tmp_path, grid_filter=None, **grid_options):
    touch(tmp_path, *[f"IMG_{i:03}.jpg" for i in range(60)])  # more than fit, so the vertical scroll bar shows
    grid = Grid(tmp_path, grid_filter=grid_filter or GridFilter(), **grid_options)
    qtbot.addWidget(grid)
    grid.keep_clear_at_the_bottom(40)  # as the window does for its status bar
    grid.resize(800, 600)
    grid.show()
    qtbot.waitExposed(grid)
    if any(not grid.isRowHidden(row) for row in range(grid.model().rowCount())):
        qtbot.waitUntil(grid.verticalScrollBar().isVisible)
    return grid


def sits_in_the_bottom_right_corner_of_the_tiles(button, grid):
    tiles = grid.viewport().geometry()  # inside the clear bottom margin and left of the scroll bar
    corner = button.geometry()
    return tiles.contains(corner) and tiles.right() - corner.right() <= 24 and tiles.bottom() - corner.bottom() <= 24


def test_a_grid_sharing_the_windows_filter_shows_a_round_filter_button_in_the_bottom_right_corner_of_its_tiles(qtbot, tmp_path):
    grid = shown_filtered_grid(qtbot, tmp_path)

    button = grid.findChild(FilterButton)

    assert (button.isVisible(), button.width() == button.height(), sits_in_the_bottom_right_corner_of_the_tiles(button, grid)) == (True, True, True)


def test_a_grid_given_no_shared_filter_shows_no_filter_button(qtbot, tmp_path):
    touch(tmp_path, "a.jpg")
    grid = Grid(tmp_path)
    qtbot.addWidget(grid)

    assert grid.findChild(FilterButton) is None


def test_after_the_grid_is_resized_the_filter_button_sits_in_the_new_bottom_right_corner_of_its_tiles(qtbot, tmp_path):
    grid = shown_filtered_grid(qtbot, tmp_path)

    grid.resize(1200, 900)

    qtbot.waitUntil(lambda: sits_in_the_bottom_right_corner_of_the_tiles(grid.findChild(FilterButton), grid))


def click(widget):
    QTest.mouseClick(widget, Qt.MouseButton.LeftButton)


def test_clicking_the_filter_button_leaves_the_keyboard_focus_on_the_grid_so_arrow_keys_still_move_the_cursor(qtbot, tmp_path):
    grid = shown_filtered_grid(qtbot, tmp_path, at=tmp_path / "IMG_000.jpg")
    grid.activateWindow()
    grid.setFocus()
    qtbot.waitUntil(grid.hasFocus)

    click(grid.findChild(FilterButton))
    for menu in grid.findChildren(QMenu):
        menu.close()
    QTest.keyClick(grid, Qt.Key.Key_Right)

    assert (grid.hasFocus(), cursor_name(grid)) == (True, "IMG_001.jpg")


def backing_over(button, colour):
    """The colour of the button's backing, beside its glyph, when drawn over a plain colour."""
    image = QImage(button.size(), QImage.Format.Format_ARGB32)
    image.fill(QColor(colour))
    button.render(image, QPoint(0, 0), renderFlags=QWidget.RenderFlag.DrawChildren)  # over the colour, as over tiles
    return image.pixelColor(button.width() // 5, button.height() // 2)


def test_with_no_filter_on_the_filter_button_has_a_translucent_dark_backing(qtbot, tmp_path):
    button = shown_filtered_grid(qtbot, tmp_path).findChild(FilterButton)

    over_white, over_black = backing_over(button, "white"), backing_over(button, "black")

    assert over_white != over_black
    assert over_white.lightness() < 200


def test_with_a_filter_on_the_filter_button_is_drawn_checked_and_opaque_in_the_highlight_colour(qtbot, tmp_path):
    grid_filter = GridFilter()
    button = shown_filtered_grid(qtbot, tmp_path, grid_filter).findChild(FilterButton)

    grid_filter.choose(NO_TAGS)

    highlight = button.palette().highlight().color()
    assert (button.isChecked(), backing_over(button, "white"), backing_over(button, "black")) == (True, highlight, highlight)


def test_with_a_filter_on_the_filter_buttons_tooltip_names_the_active_filter(qtbot, tmp_path):
    grid_filter = GridFilter()
    button = shown_filtered_grid(qtbot, tmp_path, grid_filter).findChild(FilterButton)

    grid_filter.choose(MISSING_TAGS)

    assert MISSING_TAGS in button.toolTip()


def popped_up_menu(grid):
    [menu] = [menu for menu in grid.findChildren(QMenu) if menu.isVisible()]
    return menu


def offered(menu):
    return [(action.text(), action.isChecked()) for action in menu.actions()]


def test_clicking_the_filter_button_pops_up_a_menu_offering_with_tags_and_no_tags_with_the_active_filter_checked(qtbot, tmp_path):
    grid = shown_filtered_grid(qtbot, tmp_path, chosen(NO_TAGS))

    click(grid.findChild(FilterButton))

    assert offered(popped_up_menu(grid)) == [(WITH_TAGS, False), (NO_TAGS, True)]
    assert grid.findChild(FilterButton).isChecked()


def test_the_filter_menu_offers_missing_tags_when_the_grids_library_has_required_roots(qtbot, tmp_path):
    grid = shown_filtered_grid(qtbot, tmp_path, library=Library.create(tmp_path), required_roots=("type:",))

    click(grid.findChild(FilterButton))

    assert offered(popped_up_menu(grid)) == [(WITH_TAGS, False), (NO_TAGS, False), (MISSING_TAGS, False)]


def test_the_filter_menu_doesnt_offer_missing_tags_when_the_drive_has_no_required_roots(qtbot, tmp_path):
    grid = shown_filtered_grid(qtbot, tmp_path, library=Library.create(tmp_path))

    click(grid.findChild(FilterButton))

    assert MISSING_TAGS not in [text for text, _ in offered(popped_up_menu(grid))]


def test_the_filter_menu_offers_missing_tags_when_it_is_the_active_filter_even_without_required_roots(qtbot, tmp_path):
    grid = shown_filtered_grid(qtbot, tmp_path, chosen(MISSING_TAGS), library=Library.create(tmp_path))

    click(grid.findChild(FilterButton))

    assert (MISSING_TAGS, True) in offered(popped_up_menu(grid))


def test_clicking_an_action_in_the_filter_menu_chooses_that_filter_and_closes_the_menu(qtbot, tmp_path):
    grid_filter = GridFilter()
    grid = shown_filtered_grid(qtbot, tmp_path, grid_filter)
    click(grid.findChild(FilterButton))
    menu = popped_up_menu(grid)
    qtbot.waitExposed(menu)

    [no_tags] = [action for action in menu.actions() if action.text() == NO_TAGS]
    QTest.mouseClick(menu, Qt.MouseButton.LeftButton, pos=menu.actionGeometry(no_tags).center())

    assert (grid_filter.active, menu.isVisible()) == (NO_TAGS, False)
