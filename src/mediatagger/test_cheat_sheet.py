from pathlib import Path

import pytest

from mediatagger.cheat_sheet import GRID_KEYS, LAUNCH_KEYS, VIEWER_KEYS

DESIGN = Path(__file__).parents[2] / "DESIGN.md"


def design_table_keys(screen):
    """The key column of the table under DESIGN.md's `### <screen>` heading, backticks removed, in order."""
    section = DESIGN.read_text().split(f"\n### {screen}\n", 1)[1].split("\n### ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("|")][2:]  # past the header and its rule
    return [row.split("|")[1].strip().replace("`", "") for row in rows]


@pytest.mark.parametrize(("sheet", "screen"), [(GRID_KEYS, "Grid"), (VIEWER_KEYS, "Viewer"), (LAUNCH_KEYS, "Launch")])
def test_a_screens_cheat_sheet_lists_exactly_the_keys_of_designs_table_for_that_screen_in_order_h_included(sheet, screen):
    keys = [key for key, _ in sheet]

    assert keys == design_table_keys(screen)
    assert "h" in keys
