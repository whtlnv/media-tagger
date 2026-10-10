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

    thumbnail = red_thumbnail()
    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=thumbnail)
    found = cache.lookup("Photos/beach.jpg", size=1234, mtime=1700000000.5)

    assert (found.size(), found.pixelColor(200, 100)) == (QSize(400, 200), QColor("red"))


def test_a_stored_thumbnail_is_not_returned_once_the_files_mtime_changes(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache

    thumbnail = red_thumbnail()
    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=thumbnail)

    assert cache.lookup("Photos/beach.jpg", size=1234, mtime=1700000999.0) is None


def test_a_stored_thumbnail_is_not_returned_once_the_files_size_changes(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache

    thumbnail = red_thumbnail()
    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=thumbnail)

    assert cache.lookup("Photos/beach.jpg", size=5678, mtime=1700000000.5) is None


def test_thumbnails_stored_for_two_different_files_are_each_returned_for_their_own_file(tmp_path):
    from PySide6.QtGui import QColor, QImage

    from mediatagger.thumbnail_cache import ThumbnailCache

    blue_thumbnail = QImage(400, 200, QImage.Format_RGB32)
    blue_thumbnail.fill(QColor("blue"))
    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=red_thumbnail())
    cache.store("Photos/forest.jpg", size=1234, mtime=1700000000.5, thumbnail=blue_thumbnail)
    beach = cache.lookup("Photos/beach.jpg", size=1234, mtime=1700000000.5)
    forest = cache.lookup("Photos/forest.jpg", size=1234, mtime=1700000000.5)

    assert (beach.pixelColor(200, 100), forest.pixelColor(200, 100)) == (QColor("red"), QColor("blue"))


def red_thumbnail():
    from PySide6.QtGui import QColor, QImage

    thumbnail = QImage(400, 200, QImage.Format_RGB32)
    thumbnail.fill(QColor("red"))
    return thumbnail
