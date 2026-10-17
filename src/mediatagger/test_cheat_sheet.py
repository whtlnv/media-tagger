from pathlib import Path

import pytest

from mediatagger.cheat_sheet import GRID_KEYS, LAUNCH_KEYS, VIEWER_KEYS

DESIGN = Path(__file__).parents[2] / "DESIGN.md"


def design_table_rows(screen):
    """The (key, what it does) rows of the table under DESIGN.md's `### <screen>` heading, backticks removed, in order."""
    section = DESIGN.read_text().split(f"\n### {screen}\n", 1)[1].split("\n### ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("|")][2:]  # past the header and its rule
    return [(row.split("|")[1].strip().replace("`", ""), row.split("|")[2].strip()) for row in rows]


def design_table_keys(screen):
    """The key column of the table under DESIGN.md's `### <screen>` heading, backticks removed, in order."""
    return [key for key, _ in design_table_rows(screen)]


@pytest.mark.parametrize(("sheet", "screen"), [(GRID_KEYS, "Grid"), (VIEWER_KEYS, "Viewer"), (LAUNCH_KEYS, "Launch")])
def test_a_screens_cheat_sheet_lists_exactly_the_keys_of_designs_table_for_that_screen_in_order_h_included(sheet, screen):
    keys = [key for key, _ in sheet]

    assert keys == design_table_keys(screen)
    assert "h" in keys


def test_the_grid_cheat_sheet_and_designs_grid_table_both_list_n_for_renaming_a_tag():
    assert dict(GRID_KEYS)["n"] == "rename a tag"
    assert dict(design_table_rows("Grid"))["n"] == "rename a tag"


def test_the_viewer_cheat_sheet_and_designs_viewer_table_both_list_1_to_9_as_jumping_in_ninths_and_no_key_for_0():
    for rows in (VIEWER_KEYS, design_table_rows("Viewer")):
        assert dict(rows)["1–9"] == "jump through in ninths (1 = start)"
        assert not any("0" in key for key, _ in rows)
