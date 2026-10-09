# Test Deletion Audit

Append-only record of tests removed because a delivered change retired the behavior they asserted. Each entry records the test, the behavior, the clause that retired it, and the observed failure that confirmed the contradiction.

## 2026-10-08 · `src/mediatagger/test_viewer_open.py::test_a_viewer_opened_with_no_path_shows_only_the_launch_text`
- Asserted: the launch screen shows exactly "Drop a folder or file here, or press `o` to open" (with backticks)
- Retired by: The launch screen text reads "Drop a folder or file here, or press o to open", with no backticks around the o
- Confirmed: failed with AssertionError `'Drop a folder or file here, or press o to open' != 'Drop a folder or file here, or press \`o\` to open'` after the new behavior landed
