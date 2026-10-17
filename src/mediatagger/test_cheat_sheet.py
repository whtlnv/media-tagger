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


@pytest.mark.parametrize(("sheet", "screen", "key", "meaning"), [
    pytest.param(GRID_KEYS, "Grid", "n", "rename a tag", id="grid n renames a tag"),
    pytest.param(VIEWER_KEYS, "Viewer", "1–9", "jump through in ninths (1 = start)", id="viewer 1-9 jumps in ninths"),
    pytest.param(VIEWER_KEYS, "Viewer", "0", "back to normal: zoom, turn, speed, forwards", id="viewer 0 is back to normal"),
    pytest.param(VIEWER_KEYS, "Viewer", "b", "play backwards / forwards", id="viewer b plays backwards or forwards"),
])
def test_a_screens_cheat_sheet_and_designs_table_for_that_screen_both_give_a_key_the_same_meaning(sheet, screen, key, meaning):
    for rows in (sheet, design_table_rows(screen)):
        assert dict(rows)[key] == meaning
