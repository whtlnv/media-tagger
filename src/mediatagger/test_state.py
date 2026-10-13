import json

from mediatagger.state import remember, remember_geometry, remember_search, remembered_folder, remembered_geometry


def test_remembering_the_window_geometry_keeps_the_folder_already_remembered_in_the_state_file(tmp_path):
    state = tmp_path / "mediatagger" / "state.json"
    folder = tmp_path / "drive" / "photos"
    remember(state, folder, tmp_path / "drive")
    geometry = {"x": 30, "y": 40, "width": 600, "height": 400}

    remember_geometry(state, geometry)

    assert (remembered_folder(state), remembered_geometry(state)) == (folder, geometry)


def test_remembering_a_search_adds_its_query_at_the_end_of_searches_in_the_state_file(tmp_path):
    state = tmp_path / "mediatagger" / "state.json"
    state.parent.mkdir()
    state.write_text(json.dumps({"searches": ["family"]}))

    remember_search(state, "beach -sunset")

    assert json.loads(state.read_text())["searches"] == ["family", "beach -sunset"]
