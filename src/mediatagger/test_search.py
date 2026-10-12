from mediatagger.library import Library
from mediatagger.search import search


def test_searching_a_library_for_beach_finds_a_tagged_file_whose_own_tags_include_beach(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "dunes.jpg"
    photo.touch()
    library.enter(photo, "beach family")

    assert search(library, "beach") == [photo]


def test_searching_a_library_for_beach_leaves_out_a_tagged_file_whose_tags_dont_include_beach(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "peak.jpg"
    photo.touch()
    library.enter(photo, "mountain snow")

    assert search(library, "beach") == []


def test_searching_for_beach_in_any_letter_case_finds_a_file_tagged_beach(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "dunes.jpg"
    photo.touch()
    library.enter(photo, "beach")

    assert search(library, "BeAcH") == [photo]


def test_an_exact_term_does_not_find_a_longer_tag_that_starts_with_it(tmp_path):
    library = Library.create(tmp_path)
    photo = tmp_path / "party.jpg"
    photo.touch()
    library.enter(photo, "people:anabel")

    assert search(library, "people:ana") == []
