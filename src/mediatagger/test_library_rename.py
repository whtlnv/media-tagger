import sqlite3

import pytest

from mediatagger.library import Library, Moment, tags_db_path


def test_renaming_beach_to_places_beach_replaces_beach_with_places_beach_on_a_photo_tagged_beach(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "shore.jpg"
    photo.touch()
    library.enter(photo, "beach")

    library.rename_tag("beach", "places:beach")

    assert library.tags(photo) == ["places:beach"]


def test_renaming_beach_leaves_beachy_on_a_photo_tagged_beachy(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "shore.jpg"
    photo.touch()
    library.enter(photo, "beachy")

    library.rename_tag("beach", "places:beach")

    assert library.tags(photo) == ["beachy"]


def test_renaming_beach_to_places_beach_replaces_beach_with_places_beach_on_a_folder_tagged_beach(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "holidays"
    folder.mkdir()
    library.enter(folder, "beach")

    library.rename_tag("beach", "places:beach")

    assert library.tags(folder) == ["places:beach"]


def test_renaming_beach_to_places_beach_leaves_places_beach_once_on_a_photo_tagged_both(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "shore.jpg"
    photo.touch()
    library.enter(photo, "beach places:beach")

    library.rename_tag("beach", "places:beach")

    assert library.tags(photo) == ["places:beach"]


def test_renaming_beach_to_places_beach_reports_the_two_items_tagged_beach(tmp_path):
    library = Library.create(tmp_path)
    shore = tmp_path / "shore.jpg"
    shore.touch()
    dunes = tmp_path / "dunes.jpg"
    dunes.touch()
    pier = tmp_path / "pier.jpg"
    pier.touch()
    library.enter(shore, "beach")
    library.enter(dunes, "beach")
    library.enter(pier, "beachy")

    assert library.rename_tag("beach", "places:beach") == 2


def test_renaming_beach_when_no_item_is_tagged_beach_changes_nothing_and_reports_zero_items(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "dusk.jpg"
    photo.touch()
    library.enter(photo, "sunset")

    changed = library.rename_tag("beach", "places:beach")

    assert library.tags(photo) == ["sunset"]
    assert changed == 0


def test_renaming_beach_into_places_beach_that_a_pier_already_has_replaces_beach_on_the_shore_and_reports_both_beach_items(tmp_path):
    library = Library.create(tmp_path)
    shore = tmp_path / "shore.jpg"
    shore.touch()
    dunes = tmp_path / "dunes.jpg"
    dunes.touch()
    pier = tmp_path / "pier.jpg"
    pier.touch()
    library.enter(shore, "beach")
    library.enter(dunes, "beach places:beach")
    library.enter(pier, "places:beach")

    changed = library.rename_tag("beach", "places:beach")

    assert library.tags(shore) == ["places:beach"]
    assert changed == 2


def test_renaming_beach_into_places_beach_that_a_pier_already_has_leaves_no_beach_row_in_the_tags_table(tmp_path):
    library = Library.create(tmp_path)
    shore = tmp_path / "shore.jpg"
    shore.touch()
    pier = tmp_path / "pier.jpg"
    pier.touch()
    library.enter(shore, "beach")
    library.enter(pier, "places:beach")

    library.rename_tag("beach", "places:beach")

    connection = sqlite3.connect(tags_db_path(tmp_path))
    names = [name for (name,) in connection.execute("SELECT name FROM tags")]
    connection.close()
    assert names == ["places:beach"]


def test_renaming_beach_into_places_beach_that_a_pier_already_has_moves_the_videos_beach_moment_at_12_5_s_to_places_beach(tmp_path):
    library = Library.create(tmp_path)
    video = tmp_path / "trip.mp4"
    video.touch()
    pier = tmp_path / "pier.jpg"
    pier.touch()
    library.add_chapter(video, "beach", 12.5)
    library.enter(pier, "places:beach")

    library.rename_tag("beach", "places:beach")

    assert library.moments(video) == [Moment(12.5, ["places:beach"])]


def test_renaming_beach_into_places_beach_merges_the_videos_beach_moment_at_12_5_s_into_its_places_beach_moment_at_12_s(tmp_path):
    library = Library.create(tmp_path)
    video = tmp_path / "trip.mp4"
    video.touch()
    library.add_chapter(video, "places:beach", 12.0)
    library.add_chapter(video, "beach", 12.5)

    library.rename_tag("beach", "places:beach")

    assert library.moments(video) == [Moment(12.0, ["places:beach"])]


def test_renaming_beach_into_places_beach_keeps_the_videos_beach_moment_at_13_1_s_apart_from_its_places_beach_moment_at_12_s(tmp_path):
    library = Library.create(tmp_path)
    video = tmp_path / "trip.mp4"
    video.touch()
    library.add_chapter(video, "places:beach", 12.0)
    library.add_chapter(video, "beach", 13.1)

    library.rename_tag("beach", "places:beach")

    assert library.moments(video) == [Moment(12.0, ["places:beach"]), Moment(13.1, ["places:beach"])]


def test_renaming_beach_into_places_beach_that_fails_at_its_last_write_leaves_every_items_tags_and_moments_as_they_were(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "sunset.jpg"
    photo.touch()
    library.enter(photo, "beach")
    video = tmp_path / "trip.mp4"
    video.touch()
    library.add_chapter(video, "places:beach", 12.0)
    library.add_chapter(video, "beach", 12.5)
    library.add_chapter(video, "beach", 20.0)
    connection = sqlite3.connect(tags_db_path(tmp_path))
    with connection:  # moving the old tag's moments is the rename's last step: make it fail there
        connection.execute("CREATE TRIGGER fail_rename BEFORE UPDATE ON moments BEGIN SELECT RAISE(ABORT, 'disk gone'); END")
    connection.close()

    with pytest.raises(sqlite3.DatabaseError, match="disk gone"):
        library.rename_tag("beach", "places:beach")

    assert library.tags(photo) == ["beach"]
    assert library.tags(video) == ["beach", "places:beach"]
    assert library.moments(video) == [Moment(12.0, ["places:beach"]), Moment(12.5, ["beach"]), Moment(20.0, ["beach"])]


def test_renaming_beach_into_places_beach_does_not_revive_a_beach_moment_a_build_from_before_chapters_left_on_a_video_that_now_has_only_places_beach(tmp_path):
    library = Library.create(tmp_path)
    video = tmp_path / "trip.mp4"
    video.touch()
    library.add_chapter(video, "places:beach", 12.0)
    library.add_chapter(video, "beach", 30.0)
    connection = sqlite3.connect(tags_db_path(tmp_path))
    with connection:  # as a build from before chapters would remove a tag: its moments stay behind
        connection.execute("DELETE FROM item_tags WHERE tag_id = (SELECT id FROM tags WHERE name = 'beach')")
    connection.close()

    library.rename_tag("beach", "places:beach")

    assert library.moments(video) == [Moment(12.0, ["places:beach"])]
