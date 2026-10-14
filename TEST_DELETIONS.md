# Test Deletion Audit

Append-only record of tests removed because a delivered change retired the behavior they asserted. Each entry records the test, the behavior, the clause that retired it, and the observed failure that confirmed the contradiction.

## 2026-10-12 · `src/mediatagger/test_viewer.py::test_a_viewer_shown_on_its_own_opens_not_fullscreen_and_f_enters_then_a_second_f_leaves_fullscreen`

- reason: exact duplicate of `test_a_shown_viewer_opens_not_fullscreen_and_each_f_press_toggles_it` (the same shown viewer, the same 0, 1 and 2 `f` presses, the same not-fullscreen / fullscreen / not-fullscreen expectations)
- coverage kept by: `test_a_shown_viewer_opens_not_fullscreen_and_each_f_press_toggles_it`

## 2026-10-12 · migrated `src/mediatagger/test_viewer.py::test_a_shown_viewer_opens_fullscreen_and_each_f_press_toggles_it` -> `test_a_shown_viewer_opens_not_fullscreen_and_each_f_press_toggles_it`
- Asserted: a shown viewer is fullscreen after 0 and 2 `f` presses and not after 1
- Changed: renamed; parameters flipped — not fullscreen after 0 and 2 presses, fullscreen after 1 (case ids reworded to match)
- Retired by: "A viewer shown on its own (not inside the window) opens not fullscreen; `f` enters fullscreen and a second `f` leaves it"
- Confirmed: all three cases failed with AssertionError `False is True` / `True is False` after the new behavior landed

## 2026-10-12 · migrated `src/mediatagger/test_main.py::test_running_the_mediatagger_command_on_a_folder_opens_the_fullscreen_viewer_on_its_first_item` -> `test_running_the_mediatagger_command_on_a_folder_opens_a_normal_not_fullscreen_viewer_on_its_first_item`
- Asserted: the window shown by `mediatagger <folder>` reports `fullscreen=True` and shows the folder's first item
- Changed: renamed; now asserts `fullscreen=False` (first-item assertion unchanged)
- Retired by: "With no remembered geometry, the window opens not fullscreen, about 80 % of the available screen, centred"
- Confirmed: failed with AssertionError `'fullscreen=F...entre=#ff0000' == 'fullscreen=T...entre=#ff0000'` after the new behavior landed

## 2026-10-12 · migrated `src/mediatagger/test_main.py::test_running_the_mediatagger_command_on_a_file_opens_the_fullscreen_viewer_on_that_file` -> `test_running_the_mediatagger_command_on_a_file_opens_a_normal_not_fullscreen_viewer_on_that_file`
- Asserted: the window shown by `mediatagger <file>` reports `fullscreen=True` and shows that file
- Changed: renamed; now asserts `fullscreen=False` (shown-file assertion unchanged)
- Retired by: "With no remembered geometry, the window opens not fullscreen, about 80 % of the available screen, centred"
- Confirmed: failed with AssertionError `'fullscreen=F...entre=#0000ff' == 'fullscreen=T...entre=#0000ff'` after the new behavior landed

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

## 2026-10-12 · migrated · `src/mediatagger/test_window_state.py::test_launching_the_window_with_no_path_and_no_state_file_then_closing_it_leaves_no_state_file`
- Asserted: closing a window launched with no path and no state file leaves no `state.json`
- Retired by: Phase 9a — "Closing the window writes its size and position to `state.json` under the config home"
- Migrated to: `test_launching_the_window_with_no_path_and_no_state_file_then_closing_it_leaves_a_state_file_holding_only_its_size_and_position` — same setup, now asserts the file holds only `{"geometry": …}` (no folder)

## 2026-10-14 · narrowed `src/mediatagger/test_video_controls.py::test_the_progress_bar_shows_light_text_and_a_light_track_on_a_dark_background_over_both_black_and_white_frames`
- Now `test_the_progress_bar_shows_light_text_and_a_light_filled_track_over_a_black_frame`.
- Removed assertion: pixel (295, 10) of the bar over a white frame is darkened by the backdrop (lightness < 128).
- Why: Phase 12 drops the progress bar's dark backdrop ("Over a white video frame, the progress bar outside its text and track leaves the frame white"). The black-frame checks (light text, light filled track) are unaffected and kept (migrate, not delete).
