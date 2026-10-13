import time

import pytest

from mediatagger.library import Library
from mediatagger.search import search


def _library_with_one_file(tmp_path, name, tags):
    library = Library.create(tmp_path)
    return library, _tagged_file(library, tmp_path / name, tags)


def _tagged_file(library, photo, tags):
    photo.touch()
    library.enter(photo, tags)
    return photo


def _tagged_folder(library, folder, tags):
    folder.mkdir()
    library.enter(folder, tags)
    return folder


def _quickest_search(library, query):
    """The quickest of three searches, and its results: a single search can be held up by whatever else the machine is doing."""
    timings = []
    for _ in range(3):
        started = time.perf_counter()
        results = search(library, query)
        timings.append(time.perf_counter() - started)
    return min(timings), results


@pytest.mark.parametrize("tags, query", [
    pytest.param("beach family", "beach", id="beach finds a file whose own tags include beach"),
    pytest.param("beach", "BeAcH", id="beach in any letter case finds a file tagged beach"),
    pytest.param("beach", "beach -sunset", id="beach minus sunset finds a file tagged beach that has no sunset"),
    pytest.param("pool", "beach|pool", id="beach or pool finds a file tagged only pool"),
    pytest.param("mountain snow", "-beach|pool", id="not beach or pool finds a tagged file that has neither beach nor pool"),
    pytest.param("people:ana", "people:", id="people prefix finds a file tagged people:ana"),
    pytest.param("beach", "beach -", id="a lone minus is ignored so beach minus finds a file tagged beach"),
])
def test_searching_a_library_finds_a_file_whose_tags_match_the_query(tmp_path, tags, query):
    library, photo = _library_with_one_file(tmp_path, "dunes.jpg", tags)

    assert search(library, query) == [photo]


@pytest.mark.parametrize("tags, query", [
    pytest.param("mountain snow", "beach", id="beach leaves out a tagged file whose tags dont include beach"),
    pytest.param("people:anabel", "people:ana", id="an exact term does not find a longer tag that starts with it"),
    pytest.param("beach sunset", "beach -sunset", id="beach minus sunset leaves out a file tagged both beach and sunset"),
    pytest.param("mountain snow", "beach|pool", id="beach or pool leaves out a file tagged neither beach nor pool"),
    pytest.param("pool", "-beach|pool", id="not beach or pool leaves out a file tagged pool"),
    pytest.param("pets:rex", "people:", id="people prefix leaves out a file tagged only pets:rex"),
    pytest.param("beach", "   ", id="a blank query finds nothing even in a library with tagged files"),
])
def test_searching_a_library_leaves_out_a_file_whose_tags_dont_match_the_query(tmp_path, tags, query):
    library, _ = _library_with_one_file(tmp_path, "dunes.jpg", tags)

    assert search(library, query) == []


def test_beach_family_finds_a_file_tagged_beach_inside_a_folder_tagged_family(tmp_path):
    library = Library.create(tmp_path)
    folder = _tagged_folder(library, tmp_path / "summer", "family")
    photo = _tagged_file(library, folder / "dunes.jpg", "beach")

    assert search(library, "beach family") == [photo]


def test_beach_family_leaves_out_a_file_tagged_beach_whose_folders_carry_no_family(tmp_path):
    library = Library.create(tmp_path)
    folder = tmp_path / "summer"
    folder.mkdir()
    photo = _tagged_file(library, folder / "dunes.jpg", "beach")

    assert search(library, "beach family") == []


def test_family_beach_finds_a_file_tagged_beach_inside_a_folder_tagged_family(tmp_path):
    library = Library.create(tmp_path)
    folder = _tagged_folder(library, tmp_path / "summer", "family")
    photo = _tagged_file(library, folder / "dunes.jpg", "beach")

    assert search(library, "family beach") == [photo]


def test_a_query_of_only_exclusions_never_finds_an_untagged_file_inside_a_tagged_folder(tmp_path):
    library = Library.create(tmp_path)
    folder = _tagged_folder(library, tmp_path / "summer", "family")
    (folder / "dunes.jpg").touch()

    assert search(library, "-beach") == [folder]


def test_a_file_whose_tags_were_all_removed_is_not_found_by_the_next_search(tmp_path):
    library, photo = _library_with_one_file(tmp_path, "dunes.jpg", "beach")
    library.enter(photo, "-beach")

    assert search(library, "-sunset") == []


def test_a_matching_file_inside_a_matching_folder_is_left_out_so_only_the_folder_is_found(tmp_path):
    library = Library.create(tmp_path)
    folder = _tagged_folder(library, tmp_path / "summer", "beach")
    _tagged_file(library, folder / "dunes.jpg", "beach")

    assert search(library, "beach") == [folder]


def test_a_matching_folder_inside_a_matching_folder_is_left_out_so_only_the_top_most_folder_is_found(tmp_path):
    library = Library.create(tmp_path)
    folder = _tagged_folder(library, tmp_path / "summer", "beach")
    _tagged_folder(library, folder / "day-one", "beach")

    assert search(library, "beach") == [folder]


def test_search_results_list_a_matching_folder_before_a_matching_file(tmp_path):
    library = Library.create(tmp_path)
    photo = _tagged_file(library, tmp_path / "a-dunes.jpg", "beach")
    folder = _tagged_folder(library, tmp_path / "z-summer", "beach")

    assert search(library, "beach") == [folder, photo]


def test_search_results_list_matching_files_in_natural_order_of_their_path(tmp_path):
    library = Library.create(tmp_path)
    tenth = _tagged_file(library, tmp_path / "IMG_10.jpg", "beach")
    second = _tagged_file(library, tmp_path / "IMG_2.jpg", "beach")

    assert search(library, "beach") == [second, tenth]


def test_searching_a_library_of_5000_tagged_items_returns_its_results_in_under_200_ms(tmp_path):
    library = Library.create(tmp_path)
    for album in range(50):
        folder = tmp_path / f"album-{album}"
        folder.mkdir()
        for number in range(100):
            _tagged_file(library, folder / f"IMG_{number}.jpg", f"beach year:{2000 + album}")

    fastest, results = _quickest_search(library, "beach")

    assert (fastest < 0.200, len(results)) == (True, 5000)


def test_people_prefix_over_a_library_of_5000_tagged_items_holding_1000_people_tags_returns_its_results_in_under_200_ms(tmp_path):
    library = Library.create(tmp_path)
    for album in range(50):
        folder = tmp_path / f"album-{album}"
        folder.mkdir()
        for number in range(100):
            person = (album * 100 + number) % 1000
            _tagged_file(library, folder / f"IMG_{number}.jpg", f"people:person-{person} year:{2000 + album}")

    fastest, results = _quickest_search(library, "people:")

    assert (fastest < 0.200, len(results)) == (True, 5000)


def test_searching_a_library_of_5000_tagged_items_for_beach_or_for_people_returns_its_results_in_under_50_ms(tmp_path):
    library = Library.create(tmp_path)
    for album in range(50):
        folder = tmp_path / f"album-{album}"
        folder.mkdir()
        for number in range(100):
            person = (album * 100 + number) % 1000
            _tagged_file(library, folder / f"IMG_{number}.jpg", f"beach people:person-{person} year:{2000 + album}")

    beach_fastest, beach_results = _quickest_search(library, "beach")
    people_fastest, people_results = _quickest_search(library, "people:")

    assert (beach_fastest < 0.050, len(beach_results), people_fastest < 0.050, len(people_results)) == (True, 5000, True, 5000)


def test_searching_a_schema_version_1_library_on_a_read_only_drive_finds_nothing(tmp_path):
    from mediatagger.test_library import _create_schema_version_1_library, _read_only_drive

    _create_schema_version_1_library(tmp_path, "read-only-drive")
    with _read_only_drive(tmp_path):
        library = Library.open(tmp_path)
        results = search(library, "beach")

    assert results == []
