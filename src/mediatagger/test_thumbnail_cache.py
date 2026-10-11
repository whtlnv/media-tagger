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

    assert (found.size(), solid_colour(found.pixelColor(200, 100))) == (QSize(400, 200), QColor("red"))


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

    assert (solid_colour(beach.pixelColor(200, 100)), solid_colour(forest.pixelColor(200, 100))) == (QColor("red"), QColor("blue"))


def test_a_stored_video_thumbnail_comes_back_with_its_duration(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache

    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Videos/party.mp4", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red"), duration=7.25)

    assert cache.lookup_duration("Videos/party.mp4") == 7.25


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

    assert (found.size(), solid_colour(found.pixelColor(200, 100))) == (QSize(400, 200), QColor("red"))


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

    assert solid_colour(found.pixelColor(200, 100)) == QColor("red")


def test_with_no_drive_id_a_stored_thumbnail_is_returned_again_within_the_session(tmp_path):
    from PySide6.QtGui import QColor

    from mediatagger.thumbnail_cache import open_thumbnail_cache

    cache = open_thumbnail_cache(drive_id=None, home=tmp_path / "home")

    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red"))
    found = cache.lookup("Photos/beach.jpg", size=1234, mtime=1700000000.5)

    assert solid_colour(found.pixelColor(200, 100)) == QColor("red")


def test_a_file_that_was_never_stored_is_a_miss(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache

    cache = ThumbnailCache(tmp_path / "thumbs.db")

    assert cache.lookup("Photos/never-seen.jpg", size=1234, mtime=1700000000.5) is None


def test_each_stored_video_comes_back_with_its_own_stored_duration(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache

    cache = ThumbnailCache(tmp_path / "thumbs.db")

    cache.store("Videos/long.mp4", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red"), duration=42)
    cache.store("Videos/short.mp4", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("blue"), duration=7.25)
    long_duration = cache.lookup_duration("Videos/long.mp4")
    short_duration = cache.lookup_duration("Videos/short.mp4")

    assert (long_duration, short_duration) == (42, 7.25)


def test_a_drives_cache_opened_by_its_drive_id_returns_its_thumbnails_after_being_opened_again_by_the_same_drive_id(tmp_path):
    from PySide6.QtGui import QColor

    from mediatagger.thumbnail_cache import open_thumbnail_cache

    open_thumbnail_cache(drive_id="drive-1234", home=tmp_path / "home").store(
        "Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red")
    )
    reopened = open_thumbnail_cache(drive_id="drive-1234", home=tmp_path / "home")
    found = reopened.lookup("Photos/beach.jpg", size=1234, mtime=1700000000.5)

    assert solid_colour(found.pixelColor(200, 100)) == QColor("red")


def test_with_no_drive_id_storing_a_thumbnail_writes_nothing_to_disk(monkeypatch, tmp_path):
    from mediatagger.thumbnail_cache import open_thumbnail_cache

    cache_home = Path(os.environ["XDG_CACHE_HOME"])
    working_folder = tmp_path / "working"
    working_folder.mkdir()
    monkeypatch.chdir(working_folder)

    cache = open_thumbnail_cache(drive_id=None, home=tmp_path / "home")
    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red"))

    assert (list(cache_home.rglob("*")), list(tmp_path.rglob("*"))) == ([], [working_folder])


def test_a_drives_cache_is_not_written_when_its_location_falls_on_the_apps_own_drive(monkeypatch, tmp_path):
    from mediatagger.thumbnail_cache import open_thumbnail_cache

    app_drive = tmp_path / "APP"
    app_drive.mkdir()
    monkeypatch.setenv("XDG_CACHE_HOME", str(app_drive / "cache"))

    cache = open_thumbnail_cache(drive_id="drive-1234", home=tmp_path / "home", app_drive=app_drive)
    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red"))

    assert list(app_drive.rglob("*")) == []


def test_a_drives_cache_is_not_written_when_its_location_falls_on_the_drive_being_viewed(monkeypatch, tmp_path):
    from mediatagger.thumbnail_cache import open_thumbnail_cache

    viewed_drive = tmp_path / "MEDIA"
    viewed_drive.mkdir()
    monkeypatch.setenv("XDG_CACHE_HOME", str(viewed_drive / "cache"))

    cache = open_thumbnail_cache(drive_id="drive-1234", home=tmp_path / "home", viewed_drive=viewed_drive)
    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red"))

    assert list(viewed_drive.rglob("*")) == []


def test_a_thumbnail_stored_from_a_worker_thread_is_returned_on_the_gui_thread(tmp_path):
    import threading

    from PySide6.QtGui import QColor

    from mediatagger.thumbnail_cache import ThumbnailCache

    cache = ThumbnailCache(tmp_path / "thumbs.db", root=tmp_path)
    photo = tmp_path / "Photos" / "beach.jpg"
    worker = threading.Thread(target=lambda: cache.store(photo, size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red")))
    worker.start()
    worker.join()

    assert solid_colour(cache.lookup(photo, size=1234, mtime=1700000000.5).pixelColor(200, 100)) == QColor("red")


def test_generating_through_the_cache_returns_a_stored_thumbnail_without_generating_it_again(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache, generate_through_cache

    photo = tmp_path / "beach.jpg"
    photo.write_bytes(b"a photo")
    stat = photo.stat()
    cache = ThumbnailCache(":memory:")
    cache.store(photo, stat.st_size, stat.st_mtime, solid_thumbnail("red"))
    generated = []

    thumbnail, duration, was_generated = generate_through_cache(cache, lambda path: generated.append(path), photo)

    assert (solid_colour(thumbnail.pixelColor(0, 0)).name(), duration, was_generated, generated) == ("#ff0000", None, False, [])


def test_generating_through_the_cache_generates_a_file_it_lacks_and_keeps_it_with_its_duration_for_next_time(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache, generate_through_cache

    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"a video")
    cache = ThumbnailCache(":memory:")

    first = generate_through_cache(cache, lambda path: (solid_thumbnail("blue"), 42.0), clip)
    second = generate_through_cache(cache, lambda path: (solid_thumbnail("green"), 7.0), clip)

    assert [(solid_colour(thumbnail.pixelColor(0, 0)).name(), duration, generated) for thumbnail, duration, generated in (first, second)] == [
        ("#0000ff", 42.0, True), ("#0000ff", 42.0, False),
    ]


def test_generating_through_the_cache_does_not_retry_a_file_that_got_no_thumbnail_until_it_changes(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache, generate_through_cache

    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"not a jpeg")
    cache = ThumbnailCache(":memory:")
    attempts = []

    def generate(path):
        attempts.append(path)
        return None, None

    generate_through_cache(cache, generate, broken)
    again = generate_through_cache(cache, generate, broken)
    broken.write_bytes(b"still not a jpeg, but longer")
    generate_through_cache(cache, generate, broken)

    assert (again, len(attempts)) == ((None, None, False), 2)


def test_the_files_still_to_generate_are_those_with_nothing_stored_or_changed_since(tmp_path):
    from mediatagger.thumbnail_cache import ThumbnailCache

    stored, failed, changed, new = (tmp_path / name for name in ("stored.jpg", "failed.jpg", "changed.jpg", "new.jpg"))
    for path in (stored, failed, changed, new):
        path.write_bytes(b"a photo")
    cache = ThumbnailCache(":memory:")
    for path in (stored, changed):
        cache.store(path, path.stat().st_size, path.stat().st_mtime, solid_thumbnail("red"))
    cache.store_failure(failed, failed.stat().st_size, failed.stat().st_mtime)
    changed.write_bytes(b"a photo, edited")

    assert cache.still_to_generate([stored, failed, changed, new]) == [changed, new]


def test_a_stored_thumbnail_is_kept_as_a_jpeg(tmp_path):
    import sqlite3

    from mediatagger.thumbnail_cache import ThumbnailCache

    cache = ThumbnailCache(tmp_path / "thumbs.db")
    cache.store("Photos/beach.jpg", size=1234, mtime=1700000000.5, thumbnail=solid_thumbnail("red"))
    connection = sqlite3.connect(tmp_path / "thumbs.db")
    [(blob,)] = connection.execute("SELECT png FROM thumbnails").fetchall()
    connection.close()

    assert blob[:3] == b"\xff\xd8\xff"


def test_a_thumbnail_stored_as_png_by_an_earlier_version_still_reads(tmp_path):
    import sqlite3

    from PySide6.QtCore import QBuffer

    from mediatagger.thumbnail_cache import ThumbnailCache

    ThumbnailCache(tmp_path / "thumbs.db")  # creates the table as every version does
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    solid_thumbnail("red").save(buffer, "PNG")
    connection = sqlite3.connect(tmp_path / "thumbs.db")
    with connection:
        connection.execute("INSERT INTO thumbnails VALUES (?, ?, ?, ?, ?)", ("beach.jpg", 1234, 1700000000.5, bytes(buffer.data()), None))
    connection.close()

    found = ThumbnailCache(tmp_path / "thumbs.db").lookup("beach.jpg", size=1234, mtime=1700000000.5)

    assert found.pixelColor(200, 100).name() == "#ff0000"


def solid_colour(colour):
    """The pure colour a stored pixel stands for: thumbnails are kept as JPEG, which shifts colours by a few levels."""
    from PySide6.QtGui import QColor

    return QColor(*(255 if channel >= 128 else 0 for channel in (colour.red(), colour.green(), colour.blue())))


def solid_thumbnail(color):
    from PySide6.QtGui import QColor, QImage

    thumbnail = QImage(400, 200, QImage.Format_RGB32)
    thumbnail.fill(QColor(color))
    return thumbnail
