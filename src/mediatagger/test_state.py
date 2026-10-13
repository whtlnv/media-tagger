import json

import pytest

from mediatagger.state import remember, remember_geometry, remember_search, remembered_folder, remembered_geometry


def test_remembering_the_window_geometry_keeps_the_folder_already_remembered_in_the_state_file(tmp_path):
    state = tmp_path / "mediatagger" / "state.json"
    folder = tmp_path / "drive" / "photos"
    remember(state, folder, tmp_path / "drive")
    geometry = {"x": 30, "y": 40, "width": 600, "height": 400}

    remember_geometry(state, geometry)

    assert (remembered_folder(state), remembered_geometry(state)) == (folder, geometry)


@pytest.mark.parametrize("searches, query, remembered", [
    pytest.param(["family"], "beach -sunset", ["family", "beach -sunset"], id="adds its query at the end of searches"),
    pytest.param(["beach", "family"], "beach", ["family", "beach"], id="already in searches moves it to the end instead of adding it twice"),
    pytest.param([f"query {n}" for n in range(50)], "beach", [f"query {n}" for n in range(1, 50)] + ["beach"], id="when searches holds 50 queries drops the oldest"),
])
def test_remembering_a_search_updates_searches_in_the_state_file(tmp_path, searches, query, remembered):
    state = tmp_path / "mediatagger" / "state.json"
    state.parent.mkdir()
    state.write_text(json.dumps({"searches": searches}))

    remember_search(state, query)

    assert json.loads(state.read_text())["searches"] == remembered


def test_remembering_the_last_folder_keeps_the_searches_already_remembered_in_the_state_file(tmp_path):
    state = tmp_path / "mediatagger" / "state.json"
    state.parent.mkdir()
    state.write_text(json.dumps({"searches": ["family", "beach -sunset"]}))

    remember(state, tmp_path / "drive" / "photos", tmp_path / "drive")

    assert json.loads(state.read_text())["searches"] == ["family", "beach -sunset"]
