import os
from pathlib import Path


def test_every_test_runs_with_the_cache_home_pointing_at_a_throwaway_folder_outside_the_real_home():
    cache_home = Path(os.environ["XDG_CACHE_HOME"])

    assert (cache_home.is_dir(), cache_home.is_relative_to(Path.home())) == (True, False)


def test_with_the_cache_home_set_a_drives_cache_is_thumbs_db_under_mediatagger_and_the_drive_id(monkeypatch, tmp_path):
    from mediatagger.thumbnail_cache import cache_file

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))

    assert cache_file("drive-1234", home=tmp_path / "home") == tmp_path / "cache" / "mediatagger" / "drive-1234" / "thumbs.db"


def test_with_the_cache_home_unset_a_drives_cache_is_thumbs_db_under_the_homes_dot_cache(monkeypatch, tmp_path):
    from mediatagger.thumbnail_cache import cache_file

    monkeypatch.delenv("XDG_CACHE_HOME")

    assert cache_file("drive-1234", home=tmp_path / "home") == tmp_path / "home" / ".cache" / "mediatagger" / "drive-1234" / "thumbs.db"


def test_a_stored_thumbnail_is_returned_for_a_file_whose_size_and_mtime_are_unchanged(tmp_path):
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QColor

    from mediatagger.thumbnail_cache import ThumbnailCache

    thumbnail = solid_thumbnail("red")
    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=thumbnail)
    found = cache.lookup("Photos/beach.jpg", size=1234, mtime=1700000000.5)

    assert (found.size(), found.pixelColor(200, 100)) == (QSize(400, 200), QColor("red"))


def test_a_stored_thumbnail_is_not_returned_once_the_files_mtime_changes(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache

    thumbnail = solid_thumbnail("red")
    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=thumbnail)

    assert cache.lookup("Photos/beach.jpg", size=1234, mtime=1700000999.0) is None


def test_a_stored_thumbnail_is_not_returned_once_the_files_size_changes(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache

    thumbnail = solid_thumbnail("red")
    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=thumbnail)

    assert cache.lookup("Photos/beach.jpg", size=5678, mtime=1700000000.5) is None


def test_thumbnails_stored_for_two_different_files_are_each_returned_for_their_own_file(tmp_path):
    from PySide6.QtGui import QColor

    from mediatagger.thumbnail_cache import ThumbnailCache

    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red"))
    cache.store("Photos/forest.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("blue"))
    beach = cache.lookup("Photos/beach.jpg", size=1234, mtime=1700000000.5)
    forest = cache.lookup("Photos/forest.jpg", size=1234, mtime=1700000000.5)

    assert (beach.pixelColor(200, 100), forest.pixelColor(200, 100)) == (QColor("red"), QColor("blue"))


def test_a_stored_video_thumbnail_comes_back_with_its_duration(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache

    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Videos/party.mp4", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red"), duration=7.25)

    assert cache.lookup_duration("Videos/party.mp4", size=1234, mtime=1700000000.5) == 7.25


def test_a_stored_failure_comes_back_as_no_thumbnail_rather_than_a_miss_while_the_file_is_unchanged(tmp_path):
    from mediatagger.thumbnail_cache import NO_THUMBNAIL, ThumbnailCache

    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store_failure("Photos/broken.jpg", size=1234, mtime=1700000000.5)
    found = cache.lookup("Photos/broken.jpg", size=1234, mtime=1700000000.5)

    assert (found is NO_THUMBNAIL, found is None) == (True, False)


def test_a_stored_failure_is_a_miss_once_the_files_mtime_changes(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache

    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store_failure("Photos/broken.jpg", size=1234, mtime=1700000000.5)

    assert cache.lookup("Photos/broken.jpg", size=1234, mtime=1700000999.0) is None


def test_a_thumbnail_stored_in_one_session_is_returned_after_the_cache_is_reopened(tmp_path):
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QColor

    from mediatagger.thumbnail_cache import ThumbnailCache

    ThumbnailCache(tmp_path / "thumbs.db").store(
        "Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red")
    )
    reopened = ThumbnailCache(tmp_path / "thumbs.db")
    found = reopened.lookup("Photos/beach.jpg", size=1234, mtime=1700000000.5)

    assert (found.size(), found.pixelColor(200, 100)) == (QSize(400, 200), QColor("red"))


def test_a_thumbnail_stored_while_the_drive_was_mounted_at_one_path_is_returned_when_it_is_mounted_at_another(tmp_path):
    from PySide6.QtGui import QColor

    from mediatagger.thumbnail_cache import ThumbnailCache

    original_mount = tmp_path / "original"
    new_mount = tmp_path / "new"

    ThumbnailCache(tmp_path / "thumbs.db", root=original_mount).store(
        original_mount / "Photos" / "beach.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red")
    )
    remounted = ThumbnailCache(tmp_path / "thumbs.db", root=new_mount)
    found = remounted.lookup(new_mount / "Photos" / "beach.jpg", size=1234, mtime=1700000000.5)

    assert found.pixelColor(200, 100) == QColor("red")


def test_with_no_drive_id_a_stored_thumbnail_is_returned_again_within_the_session(tmp_path):
    from PySide6.QtGui import QColor

    from mediatagger.thumbnail_cache import open_thumbnail_cache

    cache = open_thumbnail_cache(drive_id=None, home=tmp_path / "home")

    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red"))
    found = cache.lookup("Photos/beach.jpg", size=1234, mtime=1700000000.5)

    assert found.pixelColor(200, 100) == QColor("red")


def solid_thumbnail(color):
    from PySide6.QtGui import QColor, QImage

    thumbnail = QImage(400, 200, QImage.Format_RGB32)
    thumbnail.fill(QColor(color))
    return thumbnail
