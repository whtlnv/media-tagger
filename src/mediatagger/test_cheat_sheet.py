from pathlib import Path

from mediatagger.cheat_sheet import GRID_KEYS, LAUNCH_KEYS, VIEWER_KEYS

DESIGN = Path(__file__).parents[2] / "DESIGN.md"


def design_table_keys(screen):
    """The key column of the table under DESIGN.md's `### <screen>` heading, backticks removed, in order."""
    section = DESIGN.read_text().split(f"\n### {screen}\n", 1)[1].split("\n### ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("|")][2:]  # past the header and its rule
    return [row.split("|")[1].strip().replace("`", "") for row in rows]


def test_the_grids_cheat_sheet_lists_exactly_the_keys_of_designs_grid_table_in_order_h_included():
    keys = [key for key, _ in GRID_KEYS]

    assert keys == design_table_keys("Grid")
    assert "h" in keys


def test_the_viewers_cheat_sheet_lists_exactly_the_keys_of_designs_viewer_table_in_order_h_included():
    keys = [key for key, _ in VIEWER_KEYS]

    assert keys == design_table_keys("Viewer")
    assert "h" in keys


def test_the_launch_screens_cheat_sheet_lists_exactly_the_keys_of_designs_launch_table_in_order_h_included():
    keys = [key for key, _ in LAUNCH_KEYS]

    assert keys == design_table_keys("Launch")
    assert "h" in keys
