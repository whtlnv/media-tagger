from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QStyleOptionViewItem

from mediatagger.grid import MISSING_ROOTS_BADGE, MOMENTS_BADGE, TAG_BADGE, Grid
from mediatagger.icons import Icon
from mediatagger.library import Library
from mediatagger.test_folder import touch
from mediatagger.test_grid import opaque_colours, painted_texts, tile_recording
from mediatagger.test_grid_required_tags import ROOTS, PlacementRecordingPainter


def test_a_video_tile_with_3_distinct_moments_shows_a_badge_with_a_painted_white_stopwatch_before_3_and_no_stopwatch_character(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "match.mp4")
    library.add_chapter(tmp_path / "match.mp4", "goal people:ana", 10)
    library.add_chapter(tmp_path / "match.mp4", "goal", 30)
    library.add_chapter(tmp_path / "match.mp4", "save", 50)
    grid = Grid(tmp_path, library=library)
    qtbot.addWidget(grid)
    painter = tile_recording(grid, 0)

    assert f"{Icon.STOPWATCH}3" in painter.texts
    assert not any("\u23F1" in text for text in painter.texts)
    assert opaque_colours(painter.icons[Icon.STOPWATCH]) == {QColor("white").rgba()}


def test_a_video_tile_whose_video_has_no_moments_shows_no_moments_badge(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "match.mp4")
    library.enter(tmp_path / "match.mp4", "goal")
    grid = Grid(tmp_path, library=library)
    qtbot.addWidget(grid)

    assert not any(MOMENTS_BADGE in text for text in painted_texts(grid, 0))


def test_on_a_tile_with_missing_tag_and_moments_badges_they_read_left_to_right_in_the_top_row_the_moments_badge_in_the_corner(qtbot, tmp_path):
    library = Library.create(tmp_path)
    touch(tmp_path, "match.mp4")
    library.add_chapter(tmp_path / "match.mp4", "goal", 10)
    grid = Grid(tmp_path, library=library, required_roots=ROOTS)
    qtbot.addWidget(grid)
    image = QImage(200, 200, QImage.Format.Format_ARGB32)
    painter = PlacementRecordingPainter(image)
    option = QStyleOptionViewItem()
    option.rect = QRect(0, 0, 200, 200)
    grid.itemDelegate().paint(painter, option, grid.model().index(0, 0))
    painter.end()
    missing, tags, moments = (painter.placed[text] for text in (f"{MISSING_ROOTS_BADGE}2", f"{TAG_BADGE}1", f"{MOMENTS_BADGE}1"))

    assert missing.right() < tags.left() and tags.right() < moments.left()
    assert missing.top() == tags.top() == moments.top()
    assert moments.right() > 160


def test_a_results_grid_shows_the_moments_badge_on_a_result_video_with_moments(qtbot, tmp_path):
    library = Library.create(tmp_path)
    (tmp_path / "matches").mkdir()
    touch(tmp_path / "matches", "final.mp4")
    library.add_chapter(tmp_path / "matches" / "final.mp4", "goal", 10)
    library.add_chapter(tmp_path / "matches" / "final.mp4", "goal", 70)
    grid = Grid(tmp_path, library=library, paths=[tmp_path / "matches" / "final.mp4"])
    qtbot.addWidget(grid)

    assert f"{MOMENTS_BADGE}2" in painted_texts(grid, 0)
