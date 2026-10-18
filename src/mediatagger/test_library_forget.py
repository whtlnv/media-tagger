import sqlite3

from mediatagger.library import Library, tags_db_path


def _tag_names_in_tags_db(root):
    connection = sqlite3.connect(tags_db_path(root))
    try:
        return sorted(name for (name,) in connection.execute("SELECT name FROM tags"))
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
    assert _tag_names_in_tags_db(tmp_path) == ["family"]
