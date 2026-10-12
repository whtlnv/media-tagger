from mediatagger.library import Library
from mediatagger.search import search


def test_searching_a_library_for_beach_finds_a_tagged_file_whose_own_tags_include_beach(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "dunes.jpg"
    photo.touch()
    library.enter(photo, "beach family")

    assert search(library, "beach") == [photo]
