import time

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


def test_not_beach_or_pool_finds_a_tagged_file_that_has_neither_beach_nor_pool(tmp_path):
    library, photo = _library_with_one_file(tmp_path, "peak.jpg", "mountain snow")

    assert search(library, "-beach|pool") == [photo]


def test_people_prefix_finds_a_file_tagged_people_ana(tmp_path):
    library, photo = _library_with_one_file(tmp_path, "portrait.jpg", "people:ana")

    assert search(library, "people:") == [photo]


def test_people_prefix_leaves_out_a_file_tagged_only_pets_rex(tmp_path):
    library, _ = _library_with_one_file(tmp_path, "dog.jpg", "pets:rex")

    assert search(library, "people:") == []


def test_a_lone_minus_is_ignored_so_beach_minus_finds_a_file_tagged_beach(tmp_path):
    library, photo = _library_with_one_file(tmp_path, "dunes.jpg", "beach")

    assert search(library, "beach -") == [photo]


def test_a_blank_query_finds_nothing_even_in_a_library_with_tagged_files(tmp_path):
    library, _ = _library_with_one_file(tmp_path, "dunes.jpg", "beach")

    assert search(library, "   ") == []


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

    timings = []
    for _ in range(3):  # the quickest of three: a single search can be held up by whatever else the machine is doing
        started = time.perf_counter()
        results = search(library, "beach")
        timings.append(time.perf_counter() - started)

    assert (min(timings) < 0.200, len(results)) == (True, 5000)
