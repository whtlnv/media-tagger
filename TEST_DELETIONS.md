# Test Deletion Audit

Append-only record of tests removed because a delivered change retired the behavior they asserted. Each entry records the test, the behavior, the clause that retired it, and the observed failure that confirmed the contradiction.

## 2026-10-10 · `src/mediatagger/test_main.py::test_pressing_esc_in_the_mediatagger_command_makes_it_exit_cleanly`
- Asserted: pressing `Esc` in the slideshow of `mediatagger <folder>` makes the command exit cleanly
- Retired by: shipped `mediatagger <folder>` single-window item — "`Esc` switches from the slideshow to that folder's grid"
- Confirmed: failed with `subprocess.TimeoutExpired` after 30s (command kept running after `Esc`, no traceback in stderr) after the new behavior landed

## 2026-10-09 · `src/mediatagger/test_viewer_library.py::test_pressing_t_in_the_viewer_on_a_writable_drive_with_a_tag_library_opens_a_tag_prompt_showing_the_current_files_tags`
- Asserted: on a file tagged `beach family`, the tag prompt's editable input holds `beach family`
- Retired by: Tag prompt `-family` removal item — "the prompt's input starts empty and the current tags are shown beside it as text, not as editable input"
- Confirmed: failed with AssertionError `[''] == ['beach family']` after the new behavior landed

## 2026-10-08 · `src/mediatagger/test_viewer_open.py::test_a_viewer_opened_with_no_path_shows_only_the_launch_text`
- Asserted: the launch screen shows exactly "Drop a folder or file here, or press `o` to open" (with backticks)
- Retired by: The launch screen text reads "Drop a folder or file here, or press o to open", with no backticks around the o
- Confirmed: failed with AssertionError `'Drop a folder or file here, or press o to open' != 'Drop a folder or file here, or press \`o\` to open'` after the new behavior landed
