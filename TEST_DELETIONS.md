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

## 2026-10-15 · deleted · `src/mediatagger/test_window_cheat_sheet.py` — the background cheat-sheet tests
- Asserted: the cheat sheet is drawn behind the tiles and pictures — grid background shows the grid's keys (`…pressing_h_draws_text_over_the_empty_background…`), `h` again leaves the background plain, tiles' pictures unchanged, dim text in the viewer's black around the picture with the viewer's keys rather than the grid's, the launch screen's keys behind its message, the sheet kept from grid to viewer and back, and a scrolled grid redrawing the sheet in place.
- Retired by: the user's decision of 2026-10-15 after the native check — the sheet becomes a translucent panel drawn on top of everything (TODO "Phase 15 follow-up"); background painting and the grid's full repaint on scroll are removed.
- Confirmed: failed with `AttributeError: 'CheatSheet' object has no attribute 'paint'` / pixel mismatches once the overlay landed. Each behaviour that survives is re-driven by a follow-up item (hide on second `h`, viewer keys, launch keys, grid ⇄ viewer).

## 2026-10-15 · migrated · `src/mediatagger/test_window_cheat_sheet.py` — results grid, remembered state, prompts and search bar
- Asserted the sheet's shown/hidden state through the grid's background pixels (`grid_background_shows_the_grids_keys` / `grid_background_is_plain`) or `viewer.cheat_sheet.shown`.
- Retired by: the same decision — the grid and viewer no longer draw the sheet.
- Migrated to: the same tests asserting `sheet_is_shown(window)` (the window's overlay is visible); setups unchanged.

## 2026-10-15 · migrated · `src/mediatagger/test_window_cheat_sheet.py` — tests that pressed `Esc` with the sheet shown
- `test_after_pressing_h_…shows_the_sheet_from_the_start` and `test_with_the_sheet_remembered_as_shown_pressing_h_…start_without_it` reached the grid with `Esc` from the viewer, which now hides a shown sheet instead; they now start the window on the drive's folder and press `h` in the viewer (same assertions).
- `test_with_the_panel_shown_in_the_grid_opening_an_image_shows_the_viewers_keys_and_esc_back_to_the_grid_shows_the_grids_keys` → `…and_back_in_the_grid_it_shows_the_grids_keys`: `Esc` in the viewer now hides the panel first, so the test presses `Esc` twice and `h` in the grid before checking the grid's keys.
- Retired by: follow-up item "Pressing `Esc` while the panel is shown in the grid hides it and leaves the window open on the grid".

## 2026-10-15 · deleted · `src/mediatagger/test_library.py::test_a_newly_created_library_records_schema_version_2_in_its_tags_db`
- Asserted: a new library's `meta.schema_version` is `2`.
- Retired by: Phase 18 item "A newly created library records schema version 3 in its `tags.db`" (chapters need a new table).
- Confirmed: failed with `AssertionError: '3' == '2'` once new libraries record 3; replaced in place by the schema-3 test.

## 2026-10-15 · migrated · `src/mediatagger/test_library.py` — the schema 1 → 2 upgrade tests
- `test_opening_a_schema_version_1_library_upgrades_its_tags_db_in_place_to_schema_version_2` and `test_a_schema_version_1_library_reports_schema_version_2_once_it_has_been_opened` asserted a schema-1 library opens at version 2.
- Retired by: Phase 18 item "Opening a schema-version-1 library upgrades it in place to schema version 3, its drive id unchanged" — a library is now upgraded straight to the current version.
- Confirmed: both failed with `'3' == '2'` / `3 == 2` once the upgrade went to 3; migrated in place to expect 3 (setups unchanged).

## 2026-10-17 · deleted · `src/mediatagger/test_video_controls.py::test_zero_on_a_playing_video_seeks_back_to_the_start`
- Asserted: `0` on a playing video seeks back to 0:00.
- Retired by: Phase 25 item "In the viewer on a 90 s video playing at 0:30, `0` leaves it playing at about 0:30" (`1` is now the jump to 0:00; Phase 26 gives `0` a new job).
- Confirmed: failed with the bar reading `0:28 / 1:04` instead of `0:00 / 1:04` once `0` stopped seeking; replaced by the `0`-does-nothing test.

## 2026-10-17 · migrated · `src/mediatagger/test_video_controls.py::test_a_key_on_a_playing_video_whose_progress_bar_is_hidden_shows_the_bar_at_once_reading_any_change[5 …]`
- Asserted: `5` on a 64 s clip seeks to 0:32 (50 %) and shows the bar.
- Retired by: Phase 25 item "In the viewer on a 90 s video, `2` jumps to 0:10" — digits now jump in ninths.
- Migrated in place: a 90 s clip, `5` shows the bar at `0:40 / 1:30` (four ninths); the bar-shows-on-a-digit coverage is kept.

## 2026-10-17 · migrated · `src/mediatagger/test_window_delete.py::test_del_on_a_folder_tile_asks_nothing_and_leaves_the_folder_and_its_files`
- Asserted: `Del` on a folder tile asks nothing and leaves the folder and its files.
- Retired by: Phase 30 item "Pressing `Del` on a folder tile with two files in it asks `Delete folder "Photos" and the 2 files in it? It can't be undone.`"
- Migrated in place: same setup (now a shared `cursor_on_the_folder_tile` step), asserts the folder question; "answered no keeps the folder" is pinned by its own Phase 30 test.
