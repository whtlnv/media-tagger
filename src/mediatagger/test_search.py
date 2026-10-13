from mediatagger.library import Library
from mediatagger.search import search


def _library_with_one_file(tmp_path, name, tags):
    library = Library.create(tmp_path)
    photo = tmp_path / name
    photo.touch()
    library.enter(photo, tags)
    return library, photo


def test_searching_a_library_for_beach_finds_a_tagged_file_whose_own_tags_include_beach(tmp_path):
    library, photo = _library_with_one_file(tmp_path, "dunes.jpg", "beach family")

    assert search(library, "beach") == [photo]


def test_searching_a_library_for_beach_leaves_out_a_tagged_file_whose_tags_dont_include_beach(tmp_path):
    library, _ = _library_with_one_file(tmp_path, "peak.jpg", "mountain snow")

    assert search(library, "beach") == []


def test_searching_for_beach_in_any_letter_case_finds_a_file_tagged_beach(tmp_path):
    library, photo = _library_with_one_file(tmp_path, "dunes.jpg", "beach")

    assert search(library, "BeAcH") == [photo]


def test_an_exact_term_does_not_find_a_longer_tag_that_starts_with_it(tmp_path):
    library, _ = _library_with_one_file(tmp_path, "party.jpg", "people:anabel")

    assert search(library, "people:ana") == []


def test_beach_family_finds_a_file_tagged_beach_inside_a_folder_tagged_family(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "summer"
    folder.mkdir()
    library.enter(folder, "family")
    photo = folder / "dunes.jpg"
    photo.touch()
    library.enter(photo, "beach")

    assert search(library, "beach family") == [photo]


def test_beach_family_leaves_out_a_file_tagged_beach_whose_folders_carry_no_family(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "summer"
    folder.mkdir()
    photo = folder / "dunes.jpg"
    photo.touch()
    library.enter(photo, "beach")

    assert search(library, "beach family") == []


def test_beach_minus_sunset_finds_a_file_tagged_beach_that_has_no_sunset(tmp_path):
    library, photo = _library_with_one_file(tmp_path, "dunes.jpg", "beach")

    assert search(library, "beach -sunset") == [photo]


def test_beach_minus_sunset_leaves_out_a_file_tagged_both_beach_and_sunset(tmp_path):
    library, _ = _library_with_one_file(tmp_path, "dusk.jpg", "beach sunset")

    assert search(library, "beach -sunset") == []


def test_beach_or_pool_finds_a_file_tagged_only_pool(tmp_path):
    library, photo = _library_with_one_file(tmp_path, "splash.jpg", "pool")

    assert search(library, "beach|pool") == [photo]


def test_beach_or_pool_leaves_out_a_file_tagged_neither_beach_nor_pool(tmp_path):
    library, _ = _library_with_one_file(tmp_path, "peak.jpg", "mountain snow")

    assert search(library, "beach|pool") == []


def test_not_beach_or_pool_leaves_out_a_file_tagged_pool(tmp_path):
    library, _ = _library_with_one_file(tmp_path, "splash.jpg", "pool")

    assert search(library, "-beach|pool") == []
