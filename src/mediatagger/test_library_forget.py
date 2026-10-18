import shutil
import sqlite3

from mediatagger.library import Library, tags_db_path


def _rows(root, sql):
    connection = sqlite3.connect(tags_db_path(root))
    try:
        return connection.execute(sql).fetchall()
    finally:
        connection.close()


def test_forgetting_a_photo_tagged_beach_family_leaves_it_untagged_and_beach_which_only_it_had_gone_from_the_tags_table(tmp_path):
    library = Library.create(tmp_path)
    shore, garden = tmp_path / "shore.jpg", tmp_path / "garden.jpg"
    shore.touch()
    garden.touch()
    library.enter(shore, "beach family")
    library.enter(garden, "family")

    library.forget(shore)

    assert library.tags(shore) == []
    assert library.tags(garden) == ["family"]
    assert _rows(tmp_path, "SELECT name FROM tags") == [("family",)]


def test_forgetting_a_video_with_a_goal_chapter_leaves_no_moment_row_in_tags_db(tmp_path):
    library = Library.create(tmp_path)
    match = tmp_path / "match.mp4"
    match.touch()
    library.add_chapter(match, "goal", 12.3)

    library.forget(match)

    assert _rows(tmp_path, "SELECT * FROM moments") == []


def test_forgetting_what_is_gone_of_a_removed_folder_takes_its_row_and_the_rows_of_everything_under_it_at_any_depth(tmp_path):
    library = Library.create(tmp_path)
    holidays = tmp_path / "Holidays"
    beach = holidays / "Beach"
    beach.mkdir(parents=True)
    (holidays / "IMG_1.jpg").touch()
    (beach / "IMG_2.jpg").touch()
    library.enter(holidays, "summer")
    library.enter(holidays / "IMG_1.jpg", "family")
    library.enter(beach, "sea")
    library.enter(beach / "IMG_2.jpg", "sand")
    shutil.rmtree(holidays)

    library.forget_gone(holidays)

    assert _rows(tmp_path, "SELECT rel_path FROM items") == []
