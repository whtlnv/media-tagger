# TDD Prediction Mismatches

Append-only audit log of `/red` prediction mismatches and their resolutions. Newest first. Never edit or delete prior entries — that destroys the audit trail.

## 2026-10-11 20:05 · `src/mediatagger/test_main.py::test_in_the_mediatagger_command_entering_beach_for_a_folder_tile_in_the_grid_then_enter_on_a_file_inside_it_shows_beach_dimmed_in_the_viewers_tag_overlay`
- Behavior: In the shipped `mediatagger` window, pressing `t` on a folder tile, entering `beach`, then `Enter` on a file inside that folder shows `beach` dimmed in the viewer's tag overlay
- Predicted: passes (stated up front) — `main()` builds the same `Window` whose viewer re-reads effective tags on open (previous cycle), and the inherited label is already styled grey
- Actual: passed on first run (`beach brightest≈128`)
- Type: passed unexpectedly
- Resolution: Not vacuous — making `_DIMMED_LABEL_STYLE` white fails it (`assert 255 < 195`) and entering an empty tag fails it (no overlay line); the behavior was already delivered in-process, so the test is kept as an end-to-end pin over the shipped entry point and needs no green step.

## 2026-10-11 19:50 · `src/mediatagger/test_window.py::test_after_entering_beach_in_the_windows_grid_tag_prompt_on_a_folder_tile_enter_on_a_file_inside_it_shows_beach_in_the_viewers_tag_overlay`
- Behavior: Tagging a folder in the grid and then opening a file inside it shows the new inherited tags in the viewer's overlay at once
- Predicted: AssertionError — overlay shows `[]` instead of `["beach"]` (flagged up front as likely to pass, since `Viewer._show_tag_overlay` reads `library.effective_tags` live)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: Behavior already shipped — the window reuses its one `Viewer`, and `Viewer.open` ends in `_show_current_tags()`, which re-reads effective tags from the shared session library, so there is no stale cache to drive out; replacing that call with `pass` made the test fail (`[] == ['beach']`), so it was kept as a regression pin.

## 2026-10-11 19:33 · `src/mediatagger/test_viewer_tag_overlay.py::test_a_file_with_no_own_tags_in_an_untagged_folder_next_to_a_folder_tagged_zoo_shows_no_tag_overlay`
- Behavior: A file with no own and no inherited tags shows no tag overlay
- Predicted: passes (stated up front) — `TagOverlay.show` hides each label whose tag list is empty, and `effective_tags` already excludes sibling folders' tags
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: Behavior already shipped with the two-label TagOverlay; forcing `TagOverlay.show` to make labels always visible made the test fail, so it is a real regression pin (sibling `Trip` tagged, file in `Trip2`) and was kept as is.

## 2026-10-11 19:13 · `src/mediatagger/test_viewer_tag_overlay.py::test_moving_with_space_from_an_image_to_a_video_in_a_folder_tagged_aunt_shows_the_dimmed_aunt_on_top_of_the_video`
- Behavior: Moving with `Space` from an image to a video inside a tagged folder shows the dimmed inherited tags on top of the video
- Predicted: AssertionError — childAt returns the video surface, since `Viewer._show_current` raises only `tag_overlay.own` over the surface
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: `TagOverlay.show` already raises both labels, and it runs after `_refresh()` brings up the surface, so the inherited label already ends up on top; deleting that `raise_()` made the test fail with the MpvSurface on top, so the test is a real regression check (not vacuous) and was kept as is — the behavior shipped with the eb2a252 TagOverlay extraction.

## 2026-10-11 18:48 · `src/mediatagger/test_viewer_tag_overlay.py::test_a_file_with_no_own_tags_in_a_folder_tagged_aunt_shows_aunt_in_the_tag_overlay_in_the_top_right_corner`
- Behavior: A file with only inherited tags shows the viewer's tag overlay
- Predicted: passes (stated up front) — TagOverlay already shows the inherited label independently of the own label
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The two-label TagOverlay from the dimming cycle (85570f0, eb2a252) already delivered this TODO item; no variant (Space/Left, Esc from prompt) exposes a gap, so the test is kept as a pin of the PLAN.md requirement rather than rewritten into a contrived failure.

## 2026-10-11 17:04 · `src/mediatagger/test_window.py::test_while_the_windows_grid_tag_prompt_is_open_arrows_backspace_plus_and_minus_leave_the_grids_cursor_folder_and_tile_size_unchanged`
- Behavior: While the grid's tag prompt is open, arrows, `Backspace`, `+` and `-` leave the grid's cursor, folder and tile size unchanged
- Predicted: AssertionError — cursor row changes because `Down` (ignored by the QLineEdit) bubbles to the window, which forwards it to the grid
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: a probe showed `Down` and `Up` do reach the window and get forwarded, but pressing Down then Up cancelled out; reordered to Up (no-op on the top row) … Down, and it now fails as predicted (cursor at row 3, expected 0).

## 2026-10-11 16:41 · `src/mediatagger/test_window.py::test_esc_with_the_suggestion_popup_open_in_the_windows_grid_tag_prompt_closes_only_the_popup_leaving_the_prompt_open_with_its_text`
- Behavior: With the grid's tag prompt open, the first `Esc` closes the suggestion popup and leaves the prompt open
- Predicted: passes on first run — the grid opens the shared TagPrompt, whose completer popup already eats the first Esc (pinned for the viewer in test_tag_prompt.py)
- Actual: passed on first run; without the Esc it fails (`assert (True, ['b']) == (False, ['b'])`), so the pin is not vacuous. Dropping the `trip` folder from the setup makes the prompt's focus wait time out, so the folder stays
- Type: passed unexpectedly
- Resolution: The behavior arrived with the shared TagPrompt, so the test stays as a pin and /green has nothing to implement.

## 2026-10-11 16:35 · `src/mediatagger/test_window.py::test_when_saving_from_the_windows_grid_tag_prompt_fails_because_the_drive_has_gone_away_the_prompt_stays_open_with_its_text_and_the_status_bar_says_it_couldnt_save_tags`
- Behavior: When saving from the grid's tag prompt fails because the drive has gone away, the prompt stays open with its text and the status bar says `Couldn't save tags — is the drive still connected?`
- Predicted: passes on first run — the grid opens the shared TagPrompt, whose `_record_tags` already catches `sqlite3.Error`/`OSError` and shows the couldn't-save message on the window's status bar without closing
- Actual: passed on first run; without the `Library.enter` failure it fails (`assert [] == ['beach']`), so the pin is not vacuous
- Type: passed unexpectedly
- Resolution: The behavior came with the shared TagPrompt, so the test stays as a pin and /green has nothing to implement. It pins the status-bar text through the production constant `_COULDNT_SAVE_TAGS_TEXT` instead of retyping it.

## 2026-10-11 16:21 · `src/mediatagger/test_window.py::test_typing_b_in_the_windows_grid_tag_prompt_on_a_drive_whose_library_has_beach_shows_the_suggestion_popup_listing_beach`
- Behavior: Typing in the grid's tag prompt shows autocomplete suggestions from the drive's library
- Predicted: passes on first run — the grid opens the shared TagPrompt, whose `open` loads suggestions from `library.all_tags()`
- Actual: first ValueError (too many values to unpack) — `visible_suggestion_lists()` matches every visible `QAbstractItemView`, and the Grid is one; after excluding the Grid, passed on first run. Swapping the library tag to `zebra` makes it fail (no popup), so the pin is not vacuous
- Type: wrong-reason, then passed unexpectedly
- Resolution: The viewer-era helper assumes the popup is the only visible item view, which isn't true over the grid; the test filters out the Grid in place. The behavior arrived with the shared TagPrompt, so the test was kept as a pin — /green has nothing to implement.

## 2026-10-11 16:12 · `src/mediatagger/test_window.py::test_entering_minus_sunset_in_the_windows_grid_tag_prompt_removes_sunset_from_the_selected_items_own_tags`
- Behavior: Entering `-sunset` in the grid's tag prompt removes `sunset` from the selected item's own tags
- Predicted: passes on first run (no right-reason failure was possible: the grid opens the shared TagPrompt, whose Enter calls Library.enter, and that already parses `-word` as a removal)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The behavior was already delivered when the grid got the shared TagPrompt and Library.enter's `-` parsing, so this TODO item had nothing left to drive; the test was kept, not rewritten, because it asserts the real end-to-end removal through the grid rather than being vacuous. Making it fail would mean contradicting shipped behavior.

## 2026-10-11 16:00 · `src/mediatagger/test_window.py::test_entering_beach_family_in_the_windows_grid_tag_prompt_on_a_folder_tile_saves_both_as_that_folders_own_tags_and_closes_the_prompt`
- Behavior: Entering `beach family` in the grid's tag prompt on a folder tile saves both as that folder's own tags and closes the prompt
- Predicted: AssertionError — folder's own tags read back `[]` (flagged as likely to pass, since the grid uses the shared `TagPrompt`)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The window's grid opens the shared `TagPrompt`, whose Enter already runs `library.enter` and closes the prompt, and folder tagging was already in `Library`, so the behavior arrived with the earlier cycles. The assertions aren't vacuous (tags start at `[]`, prompt starts open), so the test was kept as a pin rather than rewritten.

## 2026-10-11 15:46 · `src/mediatagger/test_window.py::test_pressing_t_in_the_windows_grid_on_a_folder_tile_tagged_beach_family_opens_the_tag_prompt_showing_beach_family_above_its_empty_input`
- Behavior: Pressing `t` in the grid on a folder tile opens the tag prompt showing that folder's own tags
- Predicted: passes on first run — `Window._tag` opens the prompt on the current tile's path whatever its kind, and `Library.tags` looks up by `rel_path` regardless of `kind`
- Actual: passed on first run; removing the `library.enter` on the folder makes it fail (`assert 'beach family' in []`), so the pin is not vacuous
- Type: passed unexpectedly
- Resolution: the behavior came for free with the file-tile `t` cycle; kept the test as a pin for folder tiles — /green has nothing to implement

## 2026-10-11 15:23 · `src/mediatagger/test_grid.py::test_a_folder_tile_whose_folder_has_no_own_tags_but_whose_parent_has_tags_shows_no_tag_badge`
- Behavior: A folder tile whose folder has no own tags but whose parent has tags shows no badge
- Predicted: passes on first run — `Library.tag_counts` counts only each item's own `item_tags` rows, so the parent's tags never reach the child folder's tile
- Actual: passed on first run; also tagging `trip/day1` itself makes it fail (`assert not True`), so the pin is not vacuous
- Type: passed unexpectedly
- Resolution: badges are own-tag only by construction; kept the test as a regression pin against badges ever switching to effective (inherited) tags — /green has nothing to implement

## 2026-10-11 15:14 · `src/mediatagger/test_grid.py::test_a_folder_tile_whose_folder_has_2_own_tags_shows_a_tag_badge_with_its_count`
- Behavior: A folder tile whose folder has own tags shows a `🏷N` badge with its own-tag count
- Predicted: passes on first run — `Library.tag_counts` already counts direct child rows by `rel_path` regardless of `kind`, and `_tiles` looks counts up by name for folder tiles too
- Actual: passed on first run; removing the `library.enter` on the folder makes it fail (`'🏷2' not in ['📁', 'trip']`), so the pin is not vacuous
- Type: passed unexpectedly
- Resolution: the behavior came for free once folders became taggable (Phase 9 folder-tag items); kept the test as a pin for it rather than inventing a failing variant — /green has nothing to implement

## 2026-10-11 15:09 · `src/mediatagger/test_tag_prompt.py::test_a_tag_on_two_folders_ranks_above_a_tag_on_one_file_typing_b_lists_bird_before_beach`
- Behavior: A tag carried by two folders ranks above a tag carried by one file in the tag prompt's suggestions
- Predicted: pass (stated before running) — `Library.all_tags` orders by `COUNT(*)` of `item_tags` rows, and each tagged folder is its own `dir` row, so two folders count 2
- Actual: passed
- Type: passed unexpectedly
- Resolution: The behavior already exists because folders are counted as items in their own right, so no rewrite could make the test fail without changing which behavior it checks; I kept it as a pin, naming the tags so the alphabetical tie-break would give the opposite order (`bird` on the folders, `beach` on the file).

## 2026-10-11 15:01 · `src/mediatagger/test_tag_prompt.py::test_a_tag_on_one_folder_holding_three_files_ranks_below_a_tag_on_two_files_typing_b_lists_bird_before_beach`
- Behavior: A tag carried by one folder holding three files ranks below a tag carried by two files in the tag prompt's suggestions (the folder counts as one item)
- Predicted: pass (stated before running) — `Library.all_tags` orders by `COUNT(*)` of `item_tags` rows, and a tagged folder is one `dir` row whose files get no own tags
- Actual: passed
- Type: passed unexpectedly
- Resolution: The behavior already exists because folder tags are stored on the folder's own row (an earlier cycle), so no rewrite could make the test fail without changing which behavior it checks; I kept it as a pin against a future change that spreads folder tags onto their files or counts inherited tags.

## 2026-10-11 14:45 · `src/mediatagger/test_library.py::test_a_folders_effective_tags_include_the_own_tags_of_its_ancestor_folders_reported_as_inherited`
- Behavior: A folder's effective tags include its ancestor folders' tags as inherited
- Predicted: passes — `effective_tags` walks `path.relative_to(root).parents` with exact `rel_path` lookups, which is the same for a folder as for a file
- Actual: passes (1 passed)
- Type: passed unexpectedly (predicted, but no red state exists for this item)
- Resolution: The ancestor walk built for files already covers folders. Any rewrite that fails would have to assert behavior outside this item. Kept the test as a guard in case a future single-query rewrite of `effective_tags` (next TODO item) handles only files, e.g. by filtering on `kind = 'file'`. Commit it as test-after, not through /green.

## 2026-10-11 14:32 · `src/mediatagger/test_library.py::test_a_files_effective_tags_exclude_the_tags_of_a_sibling_folder_whose_name_is_a_prefix_of_its_parents`
- Behavior: A file's effective tags exclude the tags of folders that aren't its ancestors (sibling, and name-prefix such as `trip` for a file in `trip2/`)
- Predicted: passes — `effective_tags` already looks up each ancestor by exact `rel_path` via `Path.parents`, so no prefix/sibling leak is possible
- Actual: passes
- Type: passed unexpectedly (predicted, but no red state exists for this item)
- Resolution: The exclusion is a property of the prior ancestor-walk implementation, not missing behavior; kept the test as a regression guard against a future SQL prefix-match (`LIKE 'trip%'`) rewrite. No rewrite can make it fail without asserting wrong behavior.

## 2026-10-11 13:58 · `src/mediatagger/test_library.py::test_entering_tags_for_a_folder_directly_under_the_drives_mount_point_stores_them_while_the_mount_point_stays_untagged`
- Behavior: Entering tags for a folder directly under the drive's mount point stores them
- Predicted: no right-reason failure available — expected a pass, since `enter` skips only `path == self.root` and the existing folder test already tags `tmp_path / "trip"`
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: no rewrite can make this fail without inventing behavior beyond the item; the previous cycle's exact-equality guard already delivers it. Kept the test as a boundary guard (it fails if the mount-point check is ever widened, for example to `path.parent == root`); it should be committed as test-after rather than sent to /green.

## 2026-10-11 13:42 · `src/mediatagger/test_library.py::test_tagging_a_folder_leaves_every_file_inside_it_with_no_own_tags`
- Behavior: Tagging a folder leaves every file inside it with no own tags
- Predicted: pass. `Library.enter` writes one `items` row for the folder only, and `Library.tags` matches the exact `rel_path`, so files inside (direct and nested) have no rows
- Actual: pass
- Type: passed unexpectedly (for Red; foreseen at prediction time)
- Resolution: This item is a guard against folder tags spreading into files' own tags, not new behaviour. No honest rewrite can make it fail. Kept as a regression pin before effective tags (inherited) are added; /green has nothing to implement.

## 2026-10-11 13:35 · `src/mediatagger/test_library.py::test_a_tagged_files_row_in_items_still_records_its_kind_as_file_next_to_a_tagged_folder`
- Behavior: A tagged file is still recorded in the library as a file (`kind` `'file'`), next to a tagged folder
- Predicted: pass — `Library.enter` already chooses `kind` per path (`"dir" if path.is_dir() else "file"`, added in cb80c4a)
- Actual: pass
- Type: passed unexpectedly (for Red; foreseen at prediction time)
- Resolution: The item is a guard ("still … next to"), not new behaviour; cb80c4a's per-path `kind` already satisfies it, and no honest rewrite can make it fail without inventing behaviour. Kept as a regression guard; /green has nothing to implement.

## 2026-10-11 13:14 · `src/mediatagger/test_library.py::test_entering_beach_for_a_folder_makes_beach_its_own_tag_also_after_the_library_is_reopened`
- Behavior: Entering `beach` for a folder makes `beach` that folder's own tag when its tags are read back, also after reopening the library
- Predicted: passes on first run (`Library.enter`/`tags` key on the relative path and never check whether it is a file, so a folder is tagged like a file already)
- Actual: passes
- Type: passed unexpectedly
- Resolution: the behavior already exists; there's no honest way to make this test fail without asserting another TODO item (`kind` `'dir'` is next), so the test stays as a pin for folder tagging and /green has nothing to implement

## 2026-10-11 00:26 · `src/mediatagger/test_main.py::test_the_grid_of_the_mediatagger_command_launched_on_a_folder_shows_a_generated_thumbnail_on_an_image_tile_after_esc`
- Behavior: The shipped `mediatagger` command's grid (launch on a folder, `Esc` to the grid) shows a generated thumbnail on an image tile
- Predicted: passes on first run (a pin: the command builds the same `Window` whose grid already generates thumbnails in the window tests)
- Actual: passes
- Type: passed unexpectedly (predicted pin)
- Resolution: Kept as a pin. It isn't vacuous: when the grid's `generate` was temporarily changed to return `(None, None)`, the test failed with `'thumbnail=None' == 'thumbnail=400x200 #ff0000'`. Production was restored afterwards.

## 2026-10-10 23:39 · `src/mediatagger/test_grid.py::test_painting_a_tile_with_a_thumbnail_after_its_file_and_library_are_gone_from_disk_still_paints_its_picture_and_tag_badge`
- Behavior: Painting a tile that has a thumbnail stats, decodes and queries nothing
- Predicted: passes on first run (a pin: the delegate already paints only from `TILE_ROLE`, and tag counts are gathered when the folder is listed)
- Actual: passes
- Type: passed unexpectedly (predicted pin)
- Resolution: Kept as a pin. It isn't vacuous: when paint was temporarily changed to decode `tile.path`, the test failed with `assert None is not None` (no picture). When paint was changed to open the library and query tag counts, it failed with `sqlite3.OperationalError: unable to open database file`. Production was restored after each check.

## 2026-10-10 23:27 · `src/mediatagger/test_grid.py::test_a_tiles_tag_count_contrasts_with_its_surroundings_over_both_a_white_and_a_black_thumbnail`
- Behavior: The tag-count, ▶ and duration badges are painted on a contrasting backing, readable over both a white and a black thumbnail
- Predicted: AssertionError — the whole tag badge (🏷 + count) shows no light/dark spread over a black thumbnail
- Actual: passed — 🏷 is a colour emoji glyph (light tan, ~lightness 210), so it already contrasts with black; only the count digit is drawn in the default black pen
- Type: passed unexpectedly
- Resolution: Narrowed the measured area to the count's digits at the badge's right end; it now fails with "tag count unreadable over a black thumbnail".

## 2026-10-10 23:11 · `src/mediatagger/test_grid.py::test_an_image_tile_paints_no_duration`
- Behavior: An image tile paints no duration
- Predicted: passes on first run (predicted from reading the code, not a right-reason failure)
- Actual: passes
- Type: passed unexpectedly
- Resolution: The previous cycle already drew the duration only inside the delegate's `_Kind.VIDEO` branch, and `thumbnail_and_duration` never gives an image a duration. Even when the image tile is forced to have a duration, nothing is painted, so the item can't go red without changing the test into something contrived. Kept the test as a regression guard on the kind check.

## 2026-10-10 21:52 · `src/mediatagger/test_window_thumbnails.py::test_on_the_system_disk_the_grids_thumbnails_are_written_nowhere_on_disk`
- Behavior: On the system disk (no library), the grid's thumbnails are written nowhere on disk
- Predicted: passes — `open_thumbnail_cache(None, ...)` already returns an in-memory cache, shipped with the previous cycle's drive-cache wiring
- Actual: passes
- Type: passed unexpectedly (predicted pin)
- Resolution: Kept as a pin rather than rewriting it to fail. Breaking the no-library branch so it writes `thumbs.db` under XDG_CACHE_HOME makes it fail with `assert [.../thumbs.db] == []`, so it is not vacuous. A first break that set a fake drive id still passed, because the viewed drive `/` contains every path and the on-viewed-drive guard falls back to memory.

## 2026-10-10 19:48 · `src/mediatagger/test_grid.py::test_in_a_folders_grid_a_folder_tile_with_no_image_directly_inside_keeps_no_thumbnail`
- Behavior: In a folder's grid, a folder tile with no image directly inside keeps no thumbnail
- Predicted: AssertionError — the folder tile gets a QImage, because the grid decodes the folder's first media file (`loop.gif`, a video here) as an image
- Actual: TypeError in the Qt event loop, `cannot unpack non-iterable NoneType object` in `grid._receive`
- Type: wrong-reason
- Resolution: Qt has no GIF writer, so `QImage.save("loop.gif")` silently wrote nothing and the subfolder was empty. `_thumbnail_and_duration` then raised IndexError, and the scheduler's catch-all emitted a bare `None` that `_receive` can't unpack. That is a separate latent bug: an empty subfolder crashes the grid's result handler. Rewrote the test to write a real one-pixel GIF from its bytes; it now fails with the predicted AssertionError (a 400×400 QImage).

## 2026-10-10 19:20 · `src/mediatagger/test_grid.py::test_in_a_folders_grid_a_corrupt_images_tile_keeps_no_thumbnail_and_its_glyph_stays`
- Behavior: In a folder's grid, a corrupt image's tile keeps no thumbnail (its glyph stays)
- Predicted: pass — read before writing: `image_thumbnail` returns None for a corrupt file, the grid stores whatever is emitted, and the delegate always paints the glyph
- Actual: passed (1 passed)
- Type: passed unexpectedly (by /red's rules; foreseen here)
- Resolution: The previous cycle already delivers this, and no red is possible without production changes: today a tile cannot tell "failed" from "not tried yet", so the assertions only check None. The test uses a valid image queued after the corrupt one as its wait point, which is likely but not guaranteed. Kept it as a regression pin; it becomes a real check once the delegate paints thumbnails (Painting items).

## 2026-10-10 18:36 · `src/mediatagger/test_thumbnail_scheduler.py::test_requesting_thumbnails_that_are_all_cached_generates_nothing`
- Behavior: Requesting thumbnails that are all cached generates nothing
- Predicted: AssertionError — generate called for all three cached paths
- Actual: AttributeError in the cache-store slot ('NoneType' has no 'save') plus the assertion failure
- Type: wrong-reason
- Resolution: with a cache attached, every generated result is stored, so the fake generate must return a QImage; made it return one, and the test now fails only on the assertion.

## 2026-10-10 18:01 · `src/mediatagger/test_thumbnail_scheduler.py::test_a_thumbnail_requested_while_the_folder_is_prefetching_is_generated_before_the_remaining_prefetch`
- Behavior: A thumbnail requested while the rest of the folder is prefetching is generated before the remaining prefetch
- Predicted: pass on first run (predicted before running, after reading the code). `request` withdraws the path from `_unrequested` into `_pending`, and `_generate_next` serves `_pending` first. The right-reason alternative would have been an AssertionError with the fourth start `folder[3]`
- Actual: passed
- Type: passed unexpectedly (for a Red step; matched the prediction)
- Resolution: the behavior was already delivered by 3025692, which built the prefetch queue as a fallback behind `_pending`. The test isn't vacuous: without the `request` call the fourth start is `folder[3]`. It is kept as a regression pin rather than rewritten into a contrived failure, and `/green` has nothing to implement

## 2026-10-10 16:52 · `src/mediatagger/test_thumbnail_cache.py::test_with_no_drive_id_storing_a_thumbnail_writes_nothing_to_disk`
- Behavior: With no drive id, nothing is written to disk
- Predicted: pass on first run — `open_thumbnail_cache(None, …)` already returns a `ThumbnailCache(":memory:")` since 1d47c16
- Actual: passed
- Type: passed unexpectedly (for a Red step; matched the prediction)
- Resolution: the behavior was already delivered by the in-memory branch from the earlier "no drive id, returned again within the session" item. The test is kept as a characterization pin rather than rewritten into a contrived failure; it would fail if the no-drive-id path ever opened a file under the cache home, the home folder, or the working folder.

## 2026-10-10 15:54 · `src/mediatagger/test_thumbnail_cache.py::test_a_stored_failure_is_a_miss_once_the_files_mtime_changes`
- Behavior: A stored failure is a miss once the file's mtime changes
- Predicted: test passes (predicted before running, after reading the code). The TODO item assumed this behavior was missing, but it wasn't
- Actual: passed
- Type: passed unexpectedly (relative to the TODO item's premise)
- Resolution: `lookup` compares size/mtime for every stored entry before returning it, and `store_failure` (previous cycle) stores the same tuple shape, so mtime invalidation already covers failures. No failing version exists without testing a different behavior. The test is kept as a regression pin, and `/green` has nothing to implement

## 2026-10-10 11:30 · `src/mediatagger/test_main.py::test_pressing_esc_in_the_slideshow_and_then_esc_in_the_grid_of_the_mediatagger_command_makes_it_exit_cleanly`
- Behavior: In the shipped `mediatagger <folder>` command, `Esc` in the slideshow and then `Esc` in the grid makes it exit cleanly
- Predicted: passes on first run, because `Window._show` already connects `grid.escaped` to `close` and the window forwards keys to the shown page. The right-reason alternative would have been `subprocess.TimeoutExpired`
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: not vacuous. The same script with only the first `Esc` hits `TimeoutExpired`, so the exit depends on the grid's `Esc`. The behavior was already delivered by 107812e, so the test was kept as an end-to-end pin of the shipped command rather than rewritten into an artificial failure

## 2026-10-10 11:24 · `src/mediatagger/test_main.py::test_running_the_mediatagger_command_with_no_path_after_a_folder_was_viewed_opens_that_folders_grid`
- Behavior: Running the shipped `mediatagger` command with no path, after a folder was viewed, opens that folder's grid
- Predicted: passes on first run, since 107812e made `main()` build `Window(None)`, which already reads `state.json` from the inherited `XDG_CONFIG_HOME`. The right-reason alternative would have been an AssertionError with `grids=[]`
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: not vacuous. The same no-path run without the earlier `mediatagger <folder>` run reports `grids=[] cursor=[]`, so the test does exercise the remembered folder. The behavior was already delivered as a side effect of 107812e. The test was kept as an end-to-end pin of the shipped command rather than rewritten into an artificial failure

## 2026-10-10 10:12 · `src/mediatagger/test_window.py::test_launching_the_window_with_no_path_and_no_state_file_then_closing_it_leaves_no_state_file`
- Behavior: Launching the window with no path and no state file, then closing it, leaves no state file
- Predicted: AssertionError — `Window.__init__` calls `_record_state(None)` and writes a state file holding folder "None"
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: with the real `os.path.ismount`, `/` is a mount point that is an ancestor of both the app package and the throwaway config home, so `_is_on_the_apps_own_drive` suppresses every write. The test now injects `is_mount_point=lambda path: False` like the other state tests, and it fails as predicted. Side note: on a machine where the app and `~/.config` share the root filesystem (the Pi), the real mount check may stop the state file from ever being written. Worth checking separately.

## 2026-10-10 09:49 · `src/mediatagger/test_window.py::test_launching_the_window_with_no_path_and_no_state_file_shows_the_launch_screen`
- Behavior: Launching the window with no path and no state file shows the launch screen
- Predicted: passes on first run — `Window._remembered_folder` already returns None when the state file is missing, so the viewer's launch screen stays current
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The behavior already exists from the remembered-folder cycles (the missing-file guard in `_remembered_folder`), so no right-reason failure is possible; kept the test as a characterization pin rather than contorting it to fail.

## 2026-10-10 08:37 · `src/mediatagger/test_window.py::test_closing_the_window_shuts_down_its_viewers_video_player_and_leaves_a_backup_of_the_open_library_holding_the_entered_tag`
- Behavior: Closing the window shuts down the viewer's video player and leaves a backup of the open library
- Predicted: passes — `Window.closeEvent` already calls `viewer.close()`, which terminates mpv and calls `session.close()` to back up the library (shipped with 46ca4f6)
- Actual: passes (1 passed); it also passes when closing with the grid shown (viewer hidden). With `Window.closeEvent`'s `viewer.close()` disabled, it fails `assert <MpvHandle> is None`, so the test is not vacuous
- Type: passed unexpectedly
- Resolution: no failing slice exists for this item; kept the test as a regression pin rather than force it to fail — the TODO item is effectively already done.

## 2026-10-10 08:16 · `src/mediatagger/test_window.py::test_in_a_one_tile_wide_window_scrolled_fully_down_the_grids_last_tile_sits_at_or_above_the_status_bar`
- Behavior: In a 400x330 window (one 200px tile per row) scrolled fully down, the last tile's bottom edge is at or above the status bar's top edge
- Predicted: AssertionError — last tile's bottom at the window bottom (~331) below the status bar's top (276)
- Actual: AssertionError — 401 <= 276 (first run, before correction: 401 <= 246, because `show_exposed` resizes to 400x300, so the 400x330 resize must come after it)
- Type: right-reason mismatch
- Resolution: The grid scrolls per item, so `End` in a 328px viewport scrolls the last row only to the second slot (rows at 0 and 200), leaving the last tile's bottom at 401, past the window bottom rather than at it; with the status bar's 54px reserved, the ~274px viewport holds the last row at the top (bottom ~201), so the assertion still drives the right behavior — accepted as-is.

## 2026-10-10 08:09 · `src/mediatagger/test_window.py::test_scrolled_to_the_end_the_windows_grids_last_row_of_tiles_sits_fully_above_the_status_bar`
- Behavior: Scrolled to the end, the grid's last row of tiles sits fully above the status bar, not under it
- Predicted: AssertionError — last tile's bottom below the status bar's top (stated after the first run, not before)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The grid scrolls per item, so dragging the scroll bar to its maximum puts the last row at the top of the viewport, and `visualRect` is the label's size hint (40×15), not the tile cell. The rewrite presses `End` (the keyboard way to the end, which scrolls the last row to the viewport bottom) and measures the cell as `visualRect.topLeft()` + `gridSize()`; it now fails 400 < 246.

## 2026-10-10 07:44 · `src/mediatagger/test_window.py::test_going_from_the_windows_viewer_to_the_grid_and_back_on_the_same_drive_does_not_ask_again_to_create_its_library`
- Behavior: Going from the viewer to the grid and back on the same drive does not ask again to create its library
- Predicted: passes — the window's one shared DriveSession already keeps `declined_drives`, so re-opening the viewer on the same drive skips the question
- Actual: passes (1 passed); `Viewer.open` does reach `session.open_library`, so the test is not vacuous — the behavior already shipped with the shared-session refactor (46ca4f6) plus the existing declined-drive memory
- Type: passed unexpectedly
- Resolution: no failing slice exists for this item; kept the test as a regression pin rather than contort it into a failure — the TODO item is effectively already done.

## 2026-10-10 06:59 · `src/mediatagger/test_window.py::test_moving_the_windows_grid_cursor_onto_a_tagged_item_shows_its_own_tags_space_separated_in_the_status_bar`
- Behavior: Moving the grid cursor onto a tagged item shows its own tags, space-separated, in the status bar
- Predicted: AssertionError — the visible status bar labels hold only the library status (e.g. `MEDIATAGGER`), no `beach family`
- Actual: AssertionError — `'beach family' in []`: no status bar label is visible at all while the grid is shown
- Type: right-reason mismatch
- Resolution: The window still has no status bar of its own; the only `StatusBar` is the viewer's child and hides with the viewer when the stack switches to the grid. Accepted the failure as correct (the tags are still missing); green will need the window-owned status bar the Phase 7 notes call for.

## 2026-10-10 06:37 · `src/mediatagger/test_window.py::test_dropping_a_file_onto_the_windows_grid_starts_its_folders_slideshow_at_that_file`
- Behavior: Dropping a file onto the grid starts its folder's slideshow at that file
- Predicted: passes on first run — the folder-drop cycle wired `Grid.dropped` to `Window._open` → `viewer.open`, and `Slideshow.open` on a file already opens its folder at that file (no right-reason failure available)
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The previous cycle already delivered this behavior. It's not a vacuous pass: the test drops `y.jpg`, the second item, so a default of "first item" would fail. I kept the test as a regression pin; no production change is needed.

## 2026-10-10 04:56 · `src/mediatagger/test_window.py::test_in_the_windows_viewer_esc_after_stepping_to_the_second_item_puts_the_grid_cursor_on_the_second_item`
- Behavior: In the window's viewer, `Esc` after stepping to the second item puts the grid cursor on the second item
- Predicted: passes on first run — `Window._show_grid` already reads `viewer.slideshow.current` at Esc time (no right-reason failure available)
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The previous cycle's green already built the grid from the live slideshow position, so this item came for free; kept the test as a regression pin rather than rewriting it, because no honest rewrite of this behavior can fail.

## 2026-10-10 04:29 · `src/mediatagger/test_grid.py::test_after_a_first_grid_has_been_shown_opening_and_showing_the_grid_of_a_folder_of_5000_files_takes_under_150_ms`
- Behavior: Opening the grid of a folder of 5,000 files finishes within a time budget, with headroom over a measurement taken after the single-lookup listing
- Predicted: pass. The single-lookup listing (b959e95) already removed the per-entry stats that made the 50 ms version fail at about 125 ms.
- Actual: passed in 5 of 5 runs. Before writing the test I measured 60 warmed-up opens at 48–58 ms, with outliers at about 88 ms.
- Type: passed unexpectedly (predicted)
- Resolution: The behavior already holds, so this is a regression guard like the 5,000-tag test, not a driving test. The 150 ms budget is about 2.7× the typical time and 1.7× the worst outlier. It uses the same warm-up shape that failed reliably at 125 ms with per-entry stats. The Pi is unmeasured.

## 2026-10-10 04:25 · `src/mediatagger/test_grid.py::test_repainting_the_grid_after_one_of_its_subfolders_is_deleted_from_disk_still_draws_that_tile_with_the_folder_glyph`
- Behavior: Repainting the grid after one of its subfolders has been deleted from disk still draws that tile with the folder glyph
- Predicted: the TODO item expects an AssertionError (the tile drawn with the image glyph, since `is_dir()` returns False once the folder is gone). After reading `grid.py` first, I expected it to pass. I didn't write that prediction down before running.
- Actual: passed on its first run
- Type: passed unexpectedly
- Resolution: Commit 9cba401 already builds each tile's glyph once, in `_TileDelegate.__init__`. Its test `test_repainting_the_grid_after_its_files_are_deleted_from_disk_still_paints_their_tiles_without_reading_them` already asserts `FOLDER_GLYPH` on a deleted subfolder. No rewrite can fail for this behavior without inventing a new one, so I removed the test and wrote no new one.

## 2026-10-10 04:00 · `src/mediatagger/test_grid.py::test_after_a_first_grid_has_been_shown_opening_and_showing_the_grid_of_a_folder_of_5000_files_takes_under_50_ms`
- Behavior: Opening the grid of a folder of 5,000 files finishes within a time budget, like the 5,000-tag test
- Predicted: AssertionError `(False, 5000)` — opening and showing a 5,000-file grid takes over 200 ms because of per-entry stats and layout
- Actual: passed (flakily) — repeated runs measured 190–350 ms; profiling showed ~55 ms listing + ~70 ms constructing (repeated per-entry stats), only ~3 ms showing, plus a one-off ~145 ms Qt font load on the first widget shown in the process
- Type: passed unexpectedly
- Resolution: The noise came from the one-off font load, not the grid. I rewrote the test to show a warm-up grid first, like the tag test excludes its first keystroke, and to use the tag test's 50 ms budget. It now fails reliably at about 125 ms, which comes from the per-entry stats.

## 2026-10-10 03:16 · `src/mediatagger/test_grid.py::test_in_the_grid_plus_makes_the_tiles_bigger_than_their_starting_size_of_about_200_px`
- Behavior: In the grid, `+` makes the tiles bigger than their starting size of about 200 px
- Predicted: AssertionError — starting tile width is `TILE_SIZE` 128, not ~200
- Actual: AssertionError — but the measured width was 35: `visualRect` of an item is its text size hint (35×15), not the grid cell set by `setGridSize`
- Type: wrong-reason
- Resolution: `visualRect` doesn't measure tiles under `setGridSize`; rewrote the test to measure tile width as the x-distance between two neighbouring tiles, which now fails on 128 vs ~200 as predicted.

## 2026-10-10 02:54 · `src/mediatagger/test_grid.py::test_a_grid_with_no_library_shows_no_tag_badges`
- Behavior: A grid with no library (viewing only) shows no tag badges
- Predicted: pass — `Grid` already falls back to `{}` tag counts when `library` is None (from the `🏷3` cycle)
- Actual: pass
- Type: passed unexpectedly
- Resolution: Already implemented by the `🏷3` cycle; the test isn't vacuous (a tagged library exists on disk for the same folder, and the `🏷3` test shows the identical setup with `library=` draws a badge), so it's kept as a characterization pin that viewing-only mode never reads tags — no rewrite can make it fail without changing the behavior.

## 2026-10-10 02:50 · `src/mediatagger/test_grid.py::test_a_tile_for_an_untagged_item_shows_no_tag_badge`
- Behavior: A tile for an untagged item shows no tag badge
- Predicted: pass — `Library.tag_counts` inner-joins `item_tags`, so untagged items are absent and the delegate draws no badge
- Actual: pass
- Type: passed unexpectedly
- Resolution: The `🏷3` cycle already implemented this; the test isn't vacuous (a tagged sibling in the same grid shows badges are drawn), so it's kept as a characterization pin against a `🏷0` regression — no rewrite can make it fail without changing the behavior.

## 2026-10-10 02:37 · `src/mediatagger/test_grid.py::test_a_tile_whose_filename_fits_shows_it_whole_with_no_ellipsis`
- Behavior: A tile whose filename fits shows it whole, with no ellipsis
- Predicted: pass — `elidedText` from the prior ellipsis cycle already returns the full string when it fits
- Actual: pass
- Type: passed unexpectedly (predicted pass; no red possible)
- Resolution: Behavior was delivered as a side effect of the truncation cycle; test kept as a non-vacuous guard (fails if the name isn't drawn or is always elided), no production change needed.

## 2026-10-10 02:26 · `src/mediatagger/test_grid.py::test_an_image_tile_shows_no_play_badge`
- Behavior: An image tile shows no ▶ badge
- Predicted: pass on first run — the previous green already guarded the badge with `if is_video(entry)`
- Actual: passed on first run
- Type: passed unexpectedly (as predicted)
- Resolution: The behavior was already built by the video-badge cycle. I kept the test as a regression pin after a mutation check: with the guard replaced by `if True`, the test fails, so it is not vacuous. The guard was restored. /green has nothing to implement.

## 2026-10-10 01:46 · `src/mediatagger/test_library.py::test_a_folders_tag_counts_leave_out_tagged_items_that_live_in_other_folders_including_its_subfolders`
- Behavior: A folder's tag counts leave out tagged items that live in other folders (including its subfolders)
- Predicted: pass — `tag_counts` iterates `folder.iterdir()`, so only direct children are ever counted
- Actual: pass
- Type: passed unexpectedly (by Red's contract; prediction itself matched)
- Resolution: The behavior already exists as a side effect of iterating direct children; kept the test as a guard for the next item (single SQL query), where a prefix `LIKE` match would pull in nested items and the `holiday2` sibling — not rewritten, since forcing a failure would mean inventing behavior.

## 2026-10-10 01:20 · `src/mediatagger/test_folder.py::test_a_folder_listing_leaves_out_non_media_files`
- Behavior: A folder listing leaves out non-media files
- Predicted: pass (no right-reason failure possible) — `folder_entries` already appends `media_files`, which filters through `_is_media`
- Actual: passed
- Type: passed unexpectedly (relative to Red's contract; pass was foreseen)
- Resolution: The behavior arrived with the "subfolders first, then images and videos" cycle, which reused `media_files`. No smaller missing slice exists, so I kept the test as a pin on `folder_entries` instead of forcing a contrived failure. The TODO item needs no /green.

## 2026-10-09 23:55 · `src/mediatagger/test_main.py::test_running_the_mediatagger_command_on_a_drive_whose_tags_db_is_garbage_with_a_backup_under_xdg_data_home_asks_to_restore_over_the_shown_viewer_and_yes_shows_the_restored_tags`
- Behavior: the shipped `mediatagger <folder>` asks the restore question in a Yes/No dialog over the shown viewer by default, and Yes shows the restored tags
- Predicted: AssertionError on returncode, stderr `TypeError: 'NoneType' object is not callable` from the viewer's missing default `ask_to_restore_library`
- Actual: TypeError: 'NoneType' object is not callable raised in the test's own setup — `back_up(library)` with no `clock=` calls `None()`
- Type: wrong-reason
- Resolution: `back_up` has no default clock (only a default root); passed a fixed UTC clock in setup, re-ran, and got the predicted failure from `Viewer._offer_to_restore_library`

## 2026-10-09 23:20 · `src/mediatagger/test_viewer_backup.py::test_answering_no_to_the_restore_question_for_a_missing_tags_db_asks_the_create_library_question`
- Behavior: Answering No to the restore question for a missing `tags.db` asks the create-library question
- Predicted: passes on first run — `_open_library` already falls through from `_offer_to_restore_library` to `_agrees_to_create_library` on the missing-`tags.db` path (added by the previous cycle's green)
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The prior item's green over-delivered this behavior; no honest assertion of the item can fail, so the test is kept as a pin on the restore-then-create question order rather than rewritten.

## 2026-10-09 23:06 · `src/mediatagger/test_viewer_backup.py::test_answering_no_to_the_restore_question_says_the_library_cant_be_opened_viewing_only`
- Behavior: Answering No to the restore question for a garbage `tags.db` shows `Library on <DRIVE> can't be opened — viewing only`
- Predicted: passes on first run — the Yes cycle (1fda9fc) already made `_offer_to_restore_library` return False on decline, which falls through to `LIBRARY_CANT_BE_OPENED_TEXT`
- Actual: passed
- Type: passed unexpectedly
- Resolution: The behavior was already built in the Yes cycle, so there was nothing to rewrite the test toward. With the decline branch temporarily removed, the test failed (status showed `Library: MEDIATAGGER` + restored text). The test stays as a regression pin, and /green has nothing to add.

## 2026-10-09 22:47 · `src/mediatagger/test_viewer_backup.py::test_opening_a_folder_on_a_drive_whose_tags_db_is_garbage_with_no_backups_for_a_drive_of_that_name_asks_nothing_and_says_the_library_cant_be_opened_viewing_only`
- Behavior: Opening a folder on a drive whose `tags.db` is garbage, with no backups for a drive of that name, asks nothing and shows `Library on <DRIVE> can't be opened — viewing only`
- Predicted: pass (stated before running), because `_offer_to_restore_library` only asks when `newest_backup` finds one, and the garbage branch already shows `LIBRARY_CANT_BE_OPENED_TEXT`
- Actual: passed
- Type: passed unexpectedly
- Resolution: The restore-question cycle already built this behavior with its `if backup:` guard, so no test can fail for it without inventing new behavior. Kept the test as a pin on the no-backup path (no question asked, cant-be-opened status) instead of rewriting it.

## 2026-10-09 20:22 · `src/mediatagger/test_viewer_backup.py::test_opening_a_folder_on_a_drive_whose_library_cant_be_opened_makes_no_backup`
- Behavior: Opening a folder on a drive whose library can't be opened makes no backup
- Predicted: passes on first run, because `_open_library` returns from the `Library.open` except branch before `back_up` is reached (written in the previous cycle)
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The behavior came along with the previous cycle's happy-path backup, which put `back_up` after the guarded `Library.open`. Without a library there's nothing to back up, so no honest rewrite fails for the right reason. Kept the test as a regression guard: a backup written by mistake under `drive.name` would make `newest_backup` non-None, which the sibling test shows it detects.

## 2026-10-09 19:11 · `src/mediatagger/test_backup.py::test_backing_up_a_library_whose_tags_changed_since_the_drives_last_backup_writes_a_new_backup`
- Behavior: Backing up a library whose tags changed since that drive's last backup writes a new backup
- Predicted: passes on first run — `_duplicates_latest` only discards byte-identical copies, so a changed database is kept
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The behavior already shipped with the previous item: the unchanged-database check only drops byte-identical copies, and the 10-backup tests already depend on that. The test was kept as a non-vacuous pin of the TODO item rather than rewritten into a false failure.

## 2026-10-09 19:01 · `src/mediatagger/test_backup.py::test_backing_up_a_drive_that_has_fewer_than_10_backups_deletes_none_of_them`
- Behavior: Backing up a drive that has fewer than 10 backups deletes none of them
- Predicted: passes. The pruning slice `sorted(...)[:-BACKUPS_KEPT_PER_DRIVE]` in `back_up` is empty when there are fewer than 10 backups (predicted openly before running; a right-reason failure was not possible)
- Actual: passed
- Type: passed unexpectedly (by Red's contract; the pass itself was predicted)
- Resolution: The previous cycle's retention slice already delivered this behavior. I kept the test as a regression guard instead of forcing an artificial failure. It isn't vacuous: it makes 4 real backups and checks all 4 remain, so a prune that deleted the oldest every time, or that got the keep count wrong, would fail it.

## 2026-10-09 17:31 · `src/mediatagger/test_main.py::test_running_the_mediatagger_command_on_a_drive_whose_library_has_beach_pressing_t_and_typing_b_shows_the_suggestion_popup_listing_beach`
- Behavior: Running the shipped `mediatagger <folder>` command on a drive whose library has `beach`, pressing `t` and typing `b` shows the suggestion popup listing `beach`
- Predicted: AssertionError — stdout `suggestions=[]`, since in a standalone offscreen process the window isn't active, so the prompt lacks focus and QLineEdit never opens the completer popup
- Actual: passed — stdout `suggestions=[['beach']]`
- Type: passed unexpectedly
- Resolution: `main()` just builds the same `Viewer` the in-process tests use, and the completer popup opens offscreen without window activation, so the behaviour was already delivered by earlier cycles; the test is kept as an end-to-end pin over the shipped entry point, not rewritten, after checking it discriminates (typing `z` in the same script reports `suggestions=[]`).

## 2026-10-09 17:13 · `src/mediatagger/test_viewer_tag_prompt.py::test_with_5000_tags_in_the_library_each_keystroke_in_the_tag_prompt_updates_the_suggestions_in_under_50_ms`
- Behavior: With 5,000 tags in the library, each keystroke in the tag prompt updates the suggestions in under 50 ms
- Predicted: AssertionError — slowest keystroke ≥ 50 ms, since every keystroke rebuilds the 5,000-entry string list and the completer refilters and redraws its popup
- Actual: passed. Measured keystrokes on the dev Mac (offscreen): 22.6 ms for the first (popup first shown), then about 0.5 ms each; the popup lists `tag1200`, `tag1201`, … (100 rows)
- Type: passed unexpectedly
- Resolution: The behavior already holds. `all_tags()` is queried once when the prompt opens (`_open_tag_prompt`), and each keystroke only filters a cached Python list. The test isn't vacuous — it really drives 5,000 tags through the prompt and times each keystroke. So I kept it as a regression guard and didn't rewrite it into an artificial failure. The first keystroke leaves only about 2.2× headroom under the budget, and slower hardware (the Pi) is unmeasured.

## 2026-10-09 17:10 · `src/mediatagger/test_viewer_tag_prompt.py::test_the_suggestion_popup_opens_above_the_prompt_and_lies_entirely_inside_the_window_even_with_more_suggestions_than_fit_below_the_prompt`
- Behavior: The suggestion popup opens above the prompt and lies entirely inside the window, even with more suggestions than fit below the prompt
- Predicted: none committed — the test was run before a prediction was stated (process lapse). Unstated expectation was a possible vacuous pass, since QCompleter flips its popup above the line edit when it would overflow the screen
- Actual: AssertionError `(False, False) == (True, True)` — popup at (16,244 368x111) runs below the prompt (top y=205) and past the window's bottom (window 400x300 at origin, offscreen screen 800x800)
- Type: right-reason mismatch
- Resolution: QCompleter positions against the screen, not the window; under offscreen the fullscreen request leaves the viewer 400x300 on an 800x800 screen, so the popup fits below on screen and opens downward, out of the window. Right-reason failure; test kept as written.

## 2026-10-09 16:55 · `src/mediatagger/test_viewer_tag_prompt.py::test_on_a_paused_video_with_the_suggestion_popup_open_down_twice_and_up_highlight_the_first_suggestion_and_do_not_seek_the_video`
- Behavior: On a video item with the suggestion popup open, `↓` and `↑` move the highlight and do not seek the video
- Predicted: passes on first run — QCompleter's popup consumes `Up`/`Down` (the completer's eventFilter plus the list view), so they never reach `Viewer.keyPressEvent`, and `_tag_prompt_has_focus` already blocks arrow seeks while the prompt is open (a right-reason failure would have been AssertionError with time-pos moved ±10s from 20)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The behavior already exists. The test is not vacuous: it uses the same paused-at-20s setup as `test_pressing_down_in_the_viewer_on_a_paused_video_seeks_it_ten_seconds_back`, where `Down` does seek, and it checks both the highlight and the position. No rewrite can make it fail without contriving it, so it is kept as a regression pin.

## 2026-10-09 16:48 · `src/mediatagger/test_viewer_tag_prompt.py::test_enter_with_no_suggestion_popup_showing_saves_the_prompts_text_beach_fam_esc_enter_adds_beach_and_fam_to_the_item`
- Behavior: `Enter` with no suggestion popup showing saves the prompt's text: `beach fam`, `Esc`, `Enter` adds `beach` and `fam` to the item
- Predicted: passes on first run — `LastWordCompleter.eventFilter` only intercepts `Return` when the popup is the watched object, so once `Esc` hides the popup, `Return` reaches the prompt's existing save path (a right-reason failure would have been AssertionError with the prompt still open on `beach fam` and IMG_1 untagged)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The behavior already exists. The test is not vacuous: it confirms the popup was showing before `Esc`, and the sibling test with Enter while the popup is open shows that the item's tags stay unchanged in that case. So this test passes only if `Return` with the popup hidden saves `beach` and `fam`. Kept as a regression pin.

## 2026-10-09 16:44 · `src/mediatagger/test_viewer_tag_prompt.py::test_esc_after_the_suggestion_popup_has_been_closed_cancels_the_prompt_leaving_the_items_tags_unchanged`
- Behavior: `Esc` after the popup has been closed cancels the prompt, leaving the item's tags unchanged
- Predicted: passes on first run — once the popup hides, focus is back on the prompt, so `Viewer.keyPressEvent`'s existing "Esc with the tag prompt focused closes it" branch handles the second Esc (a right-reason failure would have been AssertionError with the prompt still showing `['fam']`)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The behavior already exists: the popup's Esc handling and the prompt's Esc cancel work together. The test is not vacuous (the sibling popup-Esc test pins the prompt as open with its text before the second Esc, so this one only passes if that Esc cancels it without saving `fam`). Kept it as a regression pin rather than inventing a failure.

## 2026-10-09 16:40 · `src/mediatagger/test_viewer_tag_prompt.py::test_accepting_a_suggestion_for_the_only_word_in_the_prompt_leaves_no_leading_space_fam_down_tab_leaves_exactly_family`
- Behavior: Accepting a suggestion for the only word in the prompt leaves no leading space: `fam`, `↓`, `Tab` leaves exactly `family` in the prompt
- Predicted: passes on first run — `LastWordCompleter._accept_highlighted` does `typed.removesuffix(word) + highlighted`, which never inserts a separator (a right-reason failure would have been AssertionError `[' family']`)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The behavior already exists from the `beach fam` Tab cycle, which replaces only the suffix. The test is not vacuous (the prompt holds `fam` before Tab, so it only passes if the suggestion is accepted with no leading space). Kept it as a regression pin rather than inventing a failure.

## 2026-10-09 16:37 · `src/mediatagger/test_viewer_tag_prompt.py::test_esc_with_the_suggestion_popup_open_closes_only_the_popup_leaving_the_prompt_open_with_its_text_and_the_viewer_running`
- Behavior: `Esc` with the suggestion popup open closes only the popup: the prompt stays open with its text and the app keeps running
- Predicted: AssertionError — Esc reaches `Viewer.keyPressEvent` and closes the tag prompt along with the popup (prompt texts `[]`)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: QCompleter's popup event filter hands Esc straight to the line edit's `event()`, which doesn't propagate it to the Viewer, then hides the popup. A probe that sent Esc through `viewer.windowHandle()` (real popup routing) gave the same result. So this is existing Qt behavior, not a vacuous test: the assertion would fail if Esc closed the prompt. Kept the test as a regression pin rather than inventing a failure.

## 2026-10-09 16:07 · `src/mediatagger/test_viewer_tag_prompt.py::test_tab_accepts_the_highlighted_suggestion_replacing_only_the_word_being_typed_beach_fam_down_tab_leaves_beach_family_and_closes_the_popup`
- Behavior: `Tab` accepts the highlighted suggestion, replacing only the word being typed: `beach fam`, `↓`, `Tab` leaves `beach family` in the prompt and closes the popup
- Predicted: AssertionError — prompt text `'family'` (QCompleter replacing the whole line with the completion on highlight/accept), popup closed
- Actual: AssertionError — `('beach fam', []) != ('beach family', [])`; text untouched, popup closed
- Type: right-reason mismatch
- Resolution: Probed: `↓` highlights `family` without changing the text, and `Tab` hides the popup (Qt's popup event filter) but inserts nothing — so the closing half is free and the missing behavior is purely inserting the highlighted suggestion into the last word. Test kept as is.

## 2026-10-09 16:02 · `src/mediatagger/test_viewer_tag_prompt.py::test_in_the_suggestion_popup_down_twice_highlights_the_second_suggestion_and_up_then_highlights_the_first`
- Behavior: In the suggestion popup, `↓` twice highlights the second suggestion and `↑` then highlights the first
- Predicted: passes on first run — QCompleter's popup event filter already moves the current row on ↓/↑ (↓ with nothing highlighted picks row 0)
- Actual: passed (1 passed)
- Type: passed unexpectedly (predicted pass)
- Resolution: Qt provides arrow-key highlighting for free; dropping one `↓` makes the test fail (`('beach', None) != ('bird', 'beach')`), so it isn't vacuous. Kept as a regression pin; nothing for /green to do.

## 2026-10-09 15:57 · `src/mediatagger/test_viewer_tag_prompt.py::test_a_tag_saved_from_the_prompt_is_suggested_the_next_time_the_prompt_opens_after_saving_zebra_on_one_item_typing_z_on_the_next_lists_zebra`
- Behavior: A tag saved from the prompt is suggested the next time the prompt opens — after saving `zebra` on one item, opening the prompt on the next item and typing `z` lists `zebra`
- Predicted: passes unexpectedly — `_open_tag_prompt` calls `library.all_tags()`, which reads the SQLite db fresh on every prompt open
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The behavior already exists because suggestions are never cached across prompt opens. Removing the save step makes the test fail at the suggestion-list unpack (`ValueError`, no popup), so it isn't vacuous. Kept it as a regression pin; nothing for /green to do.

## 2026-10-09 15:52 · `src/mediatagger/test_viewer_tag_prompt.py::test_suggestions_come_from_the_current_drives_library_after_dropping_a_folder_from_a_second_drive_with_only_zebra_typing_b_shows_no_popup_and_z_lists_zebra`
- Behavior: Suggestions come from the current drive's library — after dropping a folder from a second drive whose library has only `zebra`, typing `b` shows no popup and typing `z` lists `zebra`
- Predicted: passes unexpectedly — `_open_tag_prompt` rebuilds suggestions from `self.library` each time, and `_open_library` swaps `self.library` on drop
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The behavior already exists from the earlier library-switching and suggestion cycles. Removing the drop makes the test fail at the `b` assertion, so it isn't vacuous. Kept it as a regression pin; nothing for /green to do.

## 2026-10-09 15:20 · `src/mediatagger/test_viewer_tag_prompt.py::test_typing_a_namespace_prefix_people_colon_lists_every_tag_under_it_at_any_depth_and_not_place_mexico`
- Behavior: Typing a namespace prefix lists every tag under it at any depth: `people:` lists `people:ana` and `people:luis:jr`, not `place:mexico`
- Predicted: passes on first run — tags are stored whole, and LastWordCompleter's prefix match already treats `people:` as a plain string prefix
- Actual: passed (1 passed)
- Type: passed unexpectedly (predicted pass)
- Resolution: The behavior already falls out of the prefix completion built in earlier cycles, so no failing test can drive it. Kept the test as a characterization pin rather than inventing a different behavior.

## 2026-10-09 15:08 · `src/mediatagger/test_viewer_tag_prompt.py::test_suggestions_with_the_same_item_count_are_listed_alphabetically_with_bird_and_beach_on_2_items_each_typing_b_lists_beach_above_bird`
- Behavior: Suggestions with the same item count are listed alphabetically: with `bird` and `beach` on 2 items each, typing `b` lists `beach` above `bird`
- Predicted: pass. `all_tags` already sorts by `COUNT(*) DESC, tags.name` (since 1a2cc3a), so ties already break by name and there is no honest failing version
- Actual: passed (1 passed)
- Type: passed unexpectedly (by the skill's standard; matched my prediction)
- Resolution: Kept as a regression pin. The test enters `bird` first so it gets the lower tag id, which means removing the name tiebreaker (and falling back to id or insertion order) would list `bird` first and fail. Nothing for /green to build

## 2026-10-09 15:05 · `src/mediatagger/test_viewer_tag_prompt.py::test_suggestions_are_ordered_by_item_count_with_beach_on_3_items_and_bird_on_1_typing_b_lists_beach_above_bird`
- Behavior: with `beach` on 3 items and `bird` on 1, typing `b` lists `beach` above `bird`
- Predicted: pass. The prior green (1a2cc3a) already sorts `all_tags` by `COUNT(*) DESC, name`, so the general rule is in place and no right-reason failure was available
- Actual: passed (1 passed)
- Type: passed unexpectedly (by the skill's standard; matched my prediction)
- Resolution: The previous cycle implemented the general ordering, not a `bird`-specific case. The assertion is sound and not vacuous, so I kept the test as a regression pin (it would catch an ascending or alphabetical sort) instead of rewriting it

## 2026-10-09 14:57 · `src/mediatagger/test_viewer_tag_prompt.py::test_in_the_tag_prompt_on_a_drive_whose_library_has_beach_and_bird_typing_be_lists_beach_and_not_bird`
- Behavior: In the tag prompt on a drive whose library has `beach` and `bird`, typing `be` lists `beach` and not `bird`
- Predicted: pass — since 0933f9e the completer's list comes from `library.all_tags()`, and QCompleter's default prefix filtering narrows `be` to `beach`
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: Second attempt (the 13:54 pin never landed in the file); the list is now library-sourced, as the earlier entry anticipated, and prefix filtering is stock Qt behavior, so no honest failing version exists. Re-added and kept as a regression pin on prefix filtering; nothing for /green to build.

## 2026-10-09 13:54 · `src/mediatagger/test_viewer_tag_prompt.py::test_in_the_tag_prompt_on_a_drive_whose_library_has_beach_and_bird_typing_be_lists_beach_and_not_bird`
- Behavior: In the tag prompt on a drive whose library has `beach` and `bird`, typing `be` lists `beach` and not `bird`
- Predicted: pass — 5015f4a hardcoded `QCompleter(["beach", "bird"])`, and QCompleter's default prefix filtering already narrows `be` to `beach`
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: Not rewritten — with `beach`/`bird` as the fixture no version can go red against the hardcoded list, and switching tags would duplicate the library-sourced items ("no tags yet → no popup", "second drive → `zebra`") that will drive the hardcode out; kept as a pin on prefix filtering that will keep holding once the list comes from the library

## 2026-10-09 13:25 · `src/mediatagger/test_viewer_library.py::test_pressing_t_on_a_drive_whose_library_cant_be_opened_opens_no_tag_prompt_says_tags_cant_be_saved_here_and_leaves_the_drive_unchanged`
- Behavior: On a drive whose library can't be opened, pressing `t` opens no tag prompt, shows "Tags can't be saved here", and leaves the drive's files unchanged
- Predicted: pass — 2a89c1b's `except sqlite3.DatabaseError` returns with `self.library = None`, so `_tags_can_be_saved_here()` is False and `t` takes the existing cant-save branch
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The behavior was already delivered as a side effect of the previous cycle (a None library already means "can't save"), so no failing version exists without inventing a false requirement. Kept the test as a regression pin; there's nothing left for /green to build.

## 2026-10-09 11:43 · `src/mediatagger/test_viewer_library.py::test_pressing_t_on_a_read_only_drive_with_a_tag_library_says_tags_cant_be_saved_here_in_the_status_bar`
- Behavior: On a read-only drive with a tag library, pressing `t` also makes the status bar say "Tags can't be saved here"
- Predicted: pass — the general `else: self.cant_save_status.show()` branch from df162dc already covers read-only (`_tags_can_be_saved_here` is False when the read-only banner shows)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: Not vacuous — with the `show()` call removed it fails (`"Tags can't be saved here" not in ['Library: MEDIATAGGER', "Read-only — tags can't be saved"]`); the behavior already shipped in the previous cycle, so the test is kept as a pin and needs no green step.

## 2026-10-09 11:33 · `src/mediatagger/test_viewer_library.py::test_pressing_t_on_the_drive_the_app_runs_from_opens_no_tag_prompt_and_writes_nothing_to_that_drive`
- Behavior: On the drive the app itself runs from, pressing `t` opens no tag prompt and nothing is written to that drive
- Predicted: passes (no right-reason failure available) — `_never_holds_a_library` already treats the app's own drive as viewing only, so `library` is None and `_tags_can_be_saved_here` blocks `t`
- Actual: passes
- Type: passed unexpectedly
- Resolution: already delivered by the app-drive guard in `_open_library`; the test uses the strongest case (the app's drive already holds a tags.db) and snapshots every file on the drive. It is not vacuous, because with the default app location the library opens and `t` shows a prompt. Kept as a characterization pin; no production change needed

## 2026-10-09 11:30 · `src/mediatagger/test_viewer_library.py::test_pressing_t_on_a_folder_on_the_system_disk_opens_no_tag_prompt`
- Behavior: On the system disk (viewing only), pressing `t` opens no tag prompt
- Predicted: passes (no right-reason failure available) — `_open_library` returns before opening a library on `/`, so `library` is None and `_tags_can_be_saved_here` already blocks `t` since the "declined library" cycle
- Actual: passes
- Type: passed unexpectedly
- Resolution: the behavior was already delivered as a side effect of the `library is not None` guard; no rewrite can make this exact behavior fail, so the test is kept as a characterization pin of the system-disk case and the TODO item needs no production change

## 2026-10-09 11:20 · `src/mediatagger/test_viewer_library.py::test_on_a_read_only_drive_with_a_tag_library_the_tag_overlay_still_shows_a_files_existing_tags`
- Behavior: On a read-only drive with a tag library, the tag overlay still shows a file's existing tags
- Predicted: likely a pass, not a right-reason failure: `_open_library` already opens the library on a read-only drive (`Library.open` swallows the migration's OperationalError) and `_show_current_tags` runs after it
- Actual: passed on first run; both the read-only banner and `beach family` are shown
- Type: passed unexpectedly
- Resolution: The behavior already comes from earlier cycles (read-only `Library.open` plus `_show_current_tags` after `_open_library`). No rewrite can make it fail without faking. Kept the test as a regression pin, because only the read-only `t` handling was guarded before.

## 2026-10-09 10:57 · `src/mediatagger/test_viewer_library.py::test_after_dropping_a_folder_from_a_second_drive_with_a_tag_library_tags_entered_in_the_prompt_are_recorded_in_the_second_drives_tags_db_not_the_firsts`
- Behavior: After dropping a folder from a second drive with a tag library, tags entered in the prompt are recorded in the second drive's `tags.db`, not the first's
- Predicted: pass — `dropEvent` → `_open` → `_open_library` already replaces `self.library` with the dropped drive's library, and `_open_tag_prompt` tags through `self.library` (no right-reason failure available)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: the behavior already exists (from the "dropping a folder from a different drive switches the status bar" item); a mutation check that kept the first drive's library open across the drop turned the test red (the dropped file is not under the first drive), so it is a real end-to-end pin and was kept as-is

## 2026-10-09 10:50 · `src/mediatagger/test_viewer_library.py::test_a_file_tagged_beach_family_in_a_viewer_shows_beach_family_in_the_tag_overlay_of_a_viewer_on_a_copy_of_the_drive_at_another_root`
- Behavior: Tagging a file on a drive opened at another mount path shows the same tags as before: a viewer on a copy of the drive at a different root shows the file's tags in the overlay
- Predicted: pass — `Library._key` stores paths relative to the drive root and the viewer opens the library at the drive it views (no right-reason failure available)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: the behavior already exists (the library-level mount-path item made keys root-relative, and the viewer only passes absolute paths through); a mutation check keying by absolute path turned the test red (`[] == ['beach family']`), so it is a real end-to-end pin and was kept as-is rather than rewritten into a contrived failure

## 2026-10-09 10:44 · `src/mediatagger/test_viewer_library.py::test_moving_with_space_from_an_image_to_a_video_tagged_beach_family_shows_the_tag_overlay_on_top_of_the_video`
- Behavior: The tag overlay stays visible on top of a video item
- Predicted: none recorded — the test was run before a prediction was stated (process slip)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: the behavior already exists — `_show_current` raises `self.tag_overlay` over the surface (added with the "tag prompt above the video surface" item), and `_show_tag_overlay` raises it again; a mutation check that removed both raises turned the test red (`childAt` returned `MpvSurface`), so the test is a real pin, not vacuous, and was kept as-is

## 2026-10-09 10:28 · `src/mediatagger/test_viewer_library.py::test_after_the_window_is_resized_the_tag_overlay_is_still_a_corner_margin_from_the_top_and_right_edges`
- Behavior: After the window is resized (e.g. leaving fullscreen with `f`), the tag overlay is still `CORNER_MARGIN` from the top and right edges
- Predicted: passes on first run — `Viewer.resizeEvent` already calls `_pin_top_right(self.tag_overlay)` (added with the corner-placement item), so no right-reason red exists
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The test is not vacuous. With the `resizeEvent` re-pin removed, it fails with `assert 83 == (999 - 16)` (the overlay keeps the position it got before the window was resized). Kept the test as a passing pin. The TODO item needs no production change.

## 2026-10-09 10:23 · `src/mediatagger/test_viewer_library.py::test_the_tag_overlay_has_the_same_look_as_the_info_overlay`
- Behavior: The tag overlay has the same look as the info overlay
- Predicted: passes on first run — `tag_overlay` is built with `overlay_label`, which applies the same `LABEL_STYLE` as `info` (so no right-reason red exists)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The behavior arrived with the tag overlay itself (`viewer.py` builds it via `overlay_label`); kept the test as a pin, matching the sibling banner/status-bar look tests, and flagged the TODO item as already satisfied rather than inventing a failing test.

## 2026-10-09 09:24 · `src/mediatagger/test_viewer_library.py::test_pressing_t_on_a_video_shows_the_tag_prompt_and_its_shown_tags_above_the_video_surface`
- Behavior: Pressing `t` on a video item shows the tag prompt above the video surface
- Predicted: AssertionError — `childAt` at the prompt's centre returns the `MpvSurface` (low confidence: the prompt is created after the surface)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The test is not vacuous. Lowering the prompt and its tags label below the surface makes it fail with `childAt` returning `MpvSurface`. The behavior already holds because `_open_tag_prompt` creates the prompt and its tags label as new children after the surface exists, and Qt stacks newer siblings on top. No failing test is possible without contriving one, so the test stays as a passing pin and the TODO item needs no production change.

## 2026-10-09 08:59 · `src/mediatagger/test_viewer_library.py::test_arrow_keys_in_the_tag_prompt_open_over_a_paused_video_neither_move_the_slideshow_nor_seek_it`
- Behavior: While the tag prompt is open, `←`, `→`, `↑` and `↓` do not move the slideshow or seek a video
- Predicted: AssertionError on the `↑` iteration — the line edit ignores `↑`, so it reaches `Viewer.keyPressEvent` and seeks the paused video from 20 s to ~30 s
- Actual: AssertionError on the `↑` iteration, but `time_pos` was 0.0, not ~30
- Type: right-reason mismatch
- Resolution: The seek did happen, but +10 s from 20 s hit the end of the 30 s clip, which wrapped it to 0. Lengthened the clip to 60 s, so the failure now reads `29.6 == 20 ± 1` as predicted. `←`/`→` already pass because the focused line edit takes them.

## 2026-10-09 08:56 · `src/mediatagger/test_viewer_library.py::test_typing_p_and_m_in_the_tag_prompt_open_over_a_playing_video_neither_pauses_nor_mutes_it`
- Behavior: While the tag prompt is open over a playing video, typing `p` and `m` into the prompt neither pauses nor mutes the video
- Predicted: passes on first run — the focused `QLineEdit` takes printable `p`/`m`, so they never reach `Viewer.keyPressEvent`
- Actual: first two runs failed for the wrong reason (`wait_until_playing` TimeoutError because the drive viewer's mpv surface was never readied; then `sqlite3.OperationalError: no such table: meta` from `make_tag_library_drive`'s schema-less stub library). After the setup fixes: 1 passed
- Type: passed unexpectedly
- Resolution: Added `make_surface_ready(viewer)` and switched to `Library.create(drive)` (tag-prompt tests need a real library). The pass comes from the earlier focus cycle. The test isn't vacuous: sending the keys to the viewer instead of `viewer.focusWidget()` makes it fail. It's kept as a characterization test, and the item doesn't need a /green step.

## 2026-10-09 08:30 · `src/mediatagger/test_viewer_library.py::test_typing_space_i_p_f_m_in_the_open_tag_prompt_goes_into_it_and_leaves_the_slideshow_and_info_overlay_unchanged`
- Behavior: While the tag prompt is open, typing a space, `i`, `p`, `f` or `m` goes into the prompt: the slideshow stays on the same item, the info overlay does not toggle and the window state does not change
- Predicted: passes on first run — the focused `QLineEdit` accepts printable keys (space included), so they never reach `Viewer.keyPressEvent`
- Actual: 1 passed
- Type: passed unexpectedly
- Resolution: The previous cycle (focus on the prompt's input) already gives this behavior. The test isn't vacuous: it sends keys to `viewer.focusWidget()` as the keyboard would, so it would fail if focus stayed on the viewer. It's kept as a characterization test, and the item doesn't need a /green step. The video pause/mute clause isn't covered here.

## 2026-10-09 08:16 · `src/mediatagger/test_viewer_library.py::test_pressing_t_gives_the_tag_prompt_keyboard_focus_so_typed_keys_go_into_it`
- Behavior: Pressing `t` gives the tag prompt's input keyboard focus, so typed keys go into it straight away
- Predicted: AssertionError — prompt text is `''` not `'beach'` (no focus, keys go to the viewer)
- Actual: sqlite3.OperationalError — no such table: meta (raised inside keyPressEvent when opening the library)
- Type: wrong-reason
- Resolution: `drive_with_a_tag_library_holding_one_image` only touches an empty `tags.db`, which `Library.open` can't read; switched the setup to `Library.create(drive)`, and it now fails with the predicted AssertionError.

## 2026-10-09 07:28 · `src/mediatagger/test_viewer_library.py::test_pressing_t_in_the_viewer_on_a_file_with_no_tags_opens_the_tag_prompt_showing_no_tags`
- Behavior: In the viewer, pressing `t` on a file with no tags opens the tag prompt showing no tags
- Predicted: passes on first run (no right-reason failure available) — `_open_tag_prompt` joins `Library.tags`, which already returns `[]` for an untagged file
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The previous cycle (cf7c735) already implemented this. The test isn't vacuous, because it uses the real library and the rendered prompt, and no honest rewrite can make it fail. It's kept as a characterization test, and the TODO item doesn't need a /green step.

## 2026-10-09 07:10 · `src/mediatagger/test_library.py::test_a_tag_change_is_visible_to_a_separate_connection_to_tags_db_as_soon_as_it_is_entered`
- Behavior: A tag change is visible to a separate connection to `tags.db` as soon as it is entered, while the library stays open (each change is committed at once)
- Predicted: passes on first run — `Library.enter` opens its own connection, commits it with `with connection:` and closes it for each entry
- Actual: 1 passed
- Type: passed unexpectedly
- Resolution: Committing each change at once already follows from opening one connection per entry; kept as a test-after pin, and there's nothing for `/green` to implement.

## 2026-10-09 05:40 · `src/mediatagger/test_library.py::test_a_colon_namespaced_tag_of_any_depth_is_kept_whole`
- Behavior: A colon-namespaced tag of any depth is kept whole as one tag (`place:mexico:cancun` reports exactly `place:mexico:cancun`, not its parts)
- Predicted: passes on first run — `Library.enter` splits only on whitespace, so colons never break a token
- Actual: 1 passed
- Type: passed unexpectedly
- Resolution: The behavior already falls out of whitespace tokenizing; kept as a test-after pin, and there's nothing for `/green` to implement.

## 2026-10-09 05:30 · `src/mediatagger/test_library.py::test_hyphens_join_words_into_one_tag`
- Behavior: Hyphens join words into one tag (`day-at-beach` reports exactly `day-at-beach`)
- Predicted: passes on first run — `Library.enter` splits only on whitespace and treats only a leading `-` as removal, so an inner hyphen stays inside the word
- Actual: 1 passed
- Type: passed unexpectedly
- Resolution: The behavior already falls out of the whitespace tokenizing; kept as a test-after pin, and there's nothing for `/green` to implement.

## 2026-10-09 05:28 · `src/mediatagger/test_library.py::test_a_lone_dash_in_an_entry_is_ignored`
- Behavior: A lone `-` in an entry is ignored (`beach -` gives exactly `beach`)
- Predicted: passes on first run — a lone `-` becomes a removal of the empty string `""`, and `str.split()` never produces an empty tag to remove
- Actual: 1 passed
- Type: passed unexpectedly
- Resolution: The behavior already falls out of the existing tokenizing, so no input can make this test fail without breaking working code; it stays as a test-after pin and there's nothing for `/green` to implement.

## 2026-10-09 05:24 · `src/mediatagger/test_library.py::test_an_entry_of_only_spaces_leaves_the_files_tags_unchanged`
- Behavior: An entry of only spaces leaves the file's tags unchanged
- Predicted: passes on first run — `Library.enter` tokenizes with a no-argument `str.split()`, so `"   "` yields no words and nothing is added or removed
- Actual: 1 passed
- Type: passed unexpectedly
- Resolution: Nothing is missing, because whitespace-only input already turns into an empty add/remove set; the test can't fail without breaking working behavior, so it stays as a test-after pin and there's nothing for `/green` to implement.

## 2026-10-09 05:20 · `src/mediatagger/test_library.py::test_extra_spaces_around_and_between_entered_tags_are_ignored`
- Behavior: Extra spaces around and between entered tags are ignored (`  beach   family ` gives exactly `beach` and `family`)
- Predicted: passes on first run — `Library.enter` already tokenizes with a no-argument `str.split()`, which drops leading, trailing and repeated whitespace
- Actual: 1 passed
- Type: passed unexpectedly
- Resolution: Nothing is missing, because the space-separated tokenizing added in an earlier cycle already does this; the test can't fail without removing working behavior, so it stays as a test-after pin and there's nothing for `/green` to implement.

## 2026-10-09 05:18 · `src/mediatagger/test_library.py::test_removing_is_case_insensitive`
- Behavior: Removing is case-insensitive (`-Sunset` removes `sunset`)
- Predicted: pass (no right-reason failure available) — `enter` lowercases the whole entry text before splitting off `-` prefixes
- Actual: passed
- Type: passed unexpectedly
- Resolution: The prior cycle's `text.lower()` (commit 2682fbd) already covers removal. No rewrite can make this fail without contradicting current behavior, so the test stays as a pin and this item needs no /green.

## 2026-10-09 04:50 · `src/mediatagger/test_library.py::test_tags_entered_for_one_file_are_not_reported_for_another_file_in_the_same_library`
- Behavior: Tags entered for one file are not reported for another file in the same library
- Predicted: pass (no right-reason failure available) — `Library._tags` is already a dict keyed by path, so an untagged file falls through to `[]`
- Actual: passed
- Type: passed unexpectedly
- Resolution: The previous green step's per-path dict already delivers this isolation; no honest rewrite of this behavior can fail, so the test is kept as a regression pin and the TODO item needs no production change.

## 2026-10-09 02:10 · `src/mediatagger/test_viewer_open.py::test_opening_a_folder_on_the_drive_the_app_runs_from_that_already_has_a_tag_library_does_not_open_it_and_says_no_library_viewing_only`
- Behavior: Opening a folder on the app's own drive when that drive already has `.mediatagger/tags.db` does not open that library: the status bar says no library, viewing only
- Predicted: passes — `_open_library` checks `_never_holds_a_library` before it checks whether `.mediatagger` exists, so the previous app-drive cycle already covers this
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The behavior was already delivered by a072322's early return. No rewrite can make it fail without asserting something else, so the test stays as a regression pin for an app drive that already has a library, and there's no production change for /green.

## 2026-10-09 02:01 · `src/mediatagger/test_viewer_open.py::test_opening_a_folder_that_does_not_exist_on_a_drive_without_a_tag_library_does_not_ask_to_create_one`
- Behavior: Opening a path that can't be opened ("Can't open <name>") does not ask to create a library
- Predicted: passes on first run — `_open` returns after `_show_cant_open` (both the `is_openable` and `OSError` branches) before reaching `_open_library`
- Actual: passed, as predicted
- Type: passed unexpectedly (relative to Red's contract; the TODO item's premise is already satisfied by existing code)
- Resolution: no failing test is possible without contriving one; kept the test as a regression pin and flagged that the TODO item needs no `/green`

## 2026-10-09 01:24 · `src/mediatagger/test_viewer_open.py::test_opening_a_folder_on_a_read_only_drive_still_shows_its_slideshow_at_the_first_item`
- Behavior: Opening a folder on a read-only drive still shows its slideshow at the first item
- Predicted: passes on first run — `_open` builds the slideshow before `_open_library` checks `os.access(drive, os.W_OK)`, and the banner is a corner label that doesn't cover the centre
- Actual: passed on first run; the assertions have teeth (an unopened slideshow paints black at the centre, and a placeholder or launch text would appear among the shown labels next to the banner)
- Type: passed unexpectedly
- Resolution: Read-only handling only toggles the banner and never stops the slideshow, so the behavior already exists. Kept the test as a regression pin; making it fail would mean asserting a different behavior. `/green` has nothing to implement.

## 2026-10-09 00:58 · `src/mediatagger/test_viewer_open.py::test_opening_a_folder_on_a_writable_drive_that_has_a_tag_library_shows_no_read_only_banner`
- Behavior: Opening a folder on a writable drive that has a tag library shows no read-only banner
- Predicted: passes on first run — the previous green already sets the banner's visibility from `os.access(drive, os.W_OK)` rather than always showing it
- Actual: passed on first run; the assertion has teeth (a banner shown unconditionally would put `READ_ONLY_BANNER_TEXT` among the shown labels)
- Type: passed unexpectedly
- Resolution: The behavior was already delivered as part of the read-only banner cycle, so a failing rewrite would have to assert some other behavior. Kept the test as the negative pin for that cycle, and `/green` has nothing to implement.

## 2026-10-09 00:30 · `src/mediatagger/test_viewer_open.py::test_declining_to_create_a_tag_library_on_a_drive_still_shows_the_opened_folders_slideshow_at_its_first_item`
- Behavior: Declining "Create a tag library on <drive>?" still shows the opened folder's slideshow at its first item
- Predicted: passes on first run — `_open_library` only returns early on decline, and `_open` calls `_refresh()` afterwards regardless
- Actual: passed on first run; the assertion has teeth (the folder holds red then blue, so showing anything but the first item or a label would fail)
- Type: passed unexpectedly
- Resolution: the early `return` in `_open_library` doesn't skip the slideshow refresh, so this already holds; kept as a characterization pin rather than rewritten to fail artificially, and flagged that this TODO item needs no green step

## 2026-10-09 00:20 · `src/mediatagger/test_viewer_open.py::test_declining_to_create_a_tag_library_on_a_drive_leaves_the_drive_without_a_mediatagger_folder`
- Behavior: Declining "Create a tag library on <drive>?" leaves the drive without a `.mediatagger` folder
- Predicted: passes on first run — `_open_library` already returns before `mkdir` when `ask_to_create_library` returns False
- Actual: passed on first run; the assertion has teeth (the sibling accepting test shows the same setup with a True answer does create `.mediatagger`)
- Type: passed unexpectedly
- Resolution: the early `return` on decline from the accept cycle already implements this; kept as a characterization pin rather than rewritten to fail artificially, and flagged that this TODO item needs no green step

## 2026-10-08 23:58 · `src/mediatagger/test_viewer_open.py::test_opening_a_folder_on_a_drive_that_already_has_a_tag_library_does_not_ask_to_create_one`
- Behavior: Opening a folder on a drive whose mount point already has `.mediatagger/tags.db` does not ask to create a library
- Predicted: passes on first run (`viewer.py` only asks when `.mediatagger` is absent, so the previous green already covers this)
- Actual: passed
- Type: passed unexpectedly
- Resolution: The previous cycle's `elif not (drive / ".mediatagger").exists()` already implements this; no failing rewrite exists without driving a different behavior, so the test is left as a characterization pin and no Red was produced.

## 2026-10-08 23:47 · `src/mediatagger/test_viewer_open.py::test_dropping_a_folder_from_a_different_drive_while_viewing_switches_the_status_bar_to_that_drives_library`
- Behavior: Dropping a folder from a different drive while viewing switches the status bar to that drive's library
- Predicted: passes on first run — `dropEvent` routes through `_open`, which already walks the dropped path's parents to its mount point and sets the library label
- Actual: passed on first run; with the drop removed it fails with `['Library: MEDIATAGGER'] == ['Library: BACKUP']`, so the assertion has teeth
- Type: passed unexpectedly
- Resolution: the behavior already exists because drop and open share `_open`; kept as a characterization pin rather than rewritten to fail artificially, and flagged that this TODO item needs no green step

## 2026-10-08 23:45 · `src/mediatagger/test_viewer_open.py::test_opening_a_file_on_a_drive_names_the_same_library_in_the_status_bar_as_opening_its_folder`
- Behavior: Opening a file on a drive names the same library in the status bar as opening its folder does
- Predicted: passes on first run — `Viewer._open` already searches `(path, *path.parents)` for the mount point, so a file path finds the same drive as its folder
- Actual: passed on first run; the assertion has teeth (folder viewer shows `Library: MEDIATAGGER`, not the no-library text), the behavior simply already exists from the prior cycle's parent walk
- Type: passed unexpectedly
- Resolution: no rewrite can make it fail without inventing new behavior; kept as a characterization pin for the file-path case and flagged that this TODO item needs no green step

## 2026-10-08 22:36 · `src/mediatagger/test_main.py::test_running_the_mediatagger_command_on_a_path_that_does_not_exist_keeps_running_and_says_it_cant_open_it`
- Behavior: Running the shipped `mediatagger /no/such/path` command keeps running and shows "Can't open path" instead of exiting with an error
- Predicted: passes on first run (wrong-reason) — `main()` already forwards `Path(sys.argv[1])` to `Viewer`, whose `_open` already shows the Can't-open message for unreadable paths
- Actual: passed on first run; running the script by hand prints "Can't open path" and exits 0, so the assertion is real, not vacuous
- Type: passed unexpectedly
- Resolution: The earlier in-process Can't-open items already delivered this through the unchanged entry point, so no missing behavior is left to drive. The test stays as an end-to-end pin; it was not rewritten because any failing version would have to test some other behavior.

## 2026-10-08 22:29 · `src/mediatagger/test_viewer_open.py::test_dropping_a_readable_folder_after_cant_open_is_shown_starts_that_folders_slideshow_at_its_first_item`
- Behavior: After "Can't open <name>" is shown, dropping a readable folder onto the window starts that folder's slideshow at its first item
- Predicted: passes — `dropEvent` → `_open` builds the slideshow, and `_show_current` hides the "Can't open" placeholder once the first image decodes
- Actual: passed
- Type: passed unexpectedly
- Resolution: The behavior already exists: the drop path reuses `_open`, which sets up a new slideshow no matter what message was showing before. A temporary sabotage check confirmed the test isn't vacuous: removing the placeholder `setVisible` call in `_show_current` fails it with the "Can't open" label still shown. I kept the test as a regression pin rather than rewrite it to fail artificially.

## 2026-10-08 22:26 · `src/mediatagger/test_viewer_open.py::test_dropping_a_folder_that_does_not_exist_while_the_info_overlay_is_shown_hides_the_overlay`
- Behavior: Dropping a folder that doesn't exist while the `i` overlay is shown hides the overlay
- Predicted: passes — `_open`'s unreadable-path branch calls `_show_message`, which already hides `self.info`
- Actual: passed
- Type: passed unexpectedly
- Resolution: The behavior already exists via the shared `_show_message`. A temporary sabotage check confirmed the test isn't vacuous: removing `self.info.hide()` fails it with the overlay text still in the shown labels. I kept the test as a regression pin rather than rewrite it to fail artificially.

## 2026-10-08 22:24 · `src/mediatagger/test_viewer_open.py::test_dropping_a_folder_that_does_not_exist_while_a_video_is_showing_stops_it_hides_its_surface_and_says_it_cant_open_it`
- Behavior: Dropping a folder that doesn't exist while a video is showing stops the video, hides the video surface and shows "Can't open <name>"
- Predicted: passes — `dropEvent` already stops the video and `_open`'s unreadable-path branch routes through `_show_message`, which hides the surface
- Actual: passed
- Type: passed unexpectedly
- Resolution: The behavior already exists: b6c2fde sent the missing-path case through the shared `_show_message`, which also serves the drop path. A temporary sabotage check confirmed the test isn't vacuous: removing `surface.hide()` from `_show_message` fails it on `shows_video_surface`. I kept the test as a regression pin rather than rewrite it to fail artificially.

## 2026-10-08 22:18 · `src/mediatagger/test_viewer_open.py::test_a_viewer_opened_on_a_file_in_a_missing_folder_shows_a_cant_open_message_naming_the_file`
- Behavior: Opening the viewer on a file path that doesn't exist (in a missing folder) shows "Can't open does_not_exist.jpg" instead of crashing
- Predicted: pass — the previous cycle's `if not path.exists()` guard in `Viewer._open` covers both files and folders
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The test isn't vacuous: it drives the real viewer and checks the rendered label. The previous cycle's guard already provides the behavior, so I kept the test as a regression pin and didn't invent a failing assertion. There's nothing for /green to do.

## 2026-10-08 21:40 · `src/mediatagger/test_viewer.py::test_the_no_media_text_shown_after_dropping_an_empty_folder_onto_the_launch_screen_is_centred_in_the_window`
- Behavior: the "No images or videos in <folder>" text after dropping an empty folder onto the launch screen is centred in the window
- Predicted: AssertionError — the label keeps the longer launch text's width, so the shorter text is drawn left of centre
- Actual: passed unexpectedly — the offscreen launch viewer is 100×30, so the launch-sized label overflows both edges and lit pixels span the full width, making the bounding-box centre coincide with the window centre
- Type: passed unexpectedly
- Resolution: resized the window to 600×500 before dropping (like the Unsupported-placeholder centring test); it now fails with the text centre 54px off

## 2026-10-08 21:18 · `src/mediatagger/test_main.py::test_dropping_a_folder_onto_the_mediatagger_command_started_with_no_path_starts_its_slideshow_at_its_first_item`
- Behavior: In the shipped `mediatagger` command started with no path, dropping a folder onto the window starts its slideshow at its first item
- Predicted: passes on first run (`main()` builds `Viewer(None)`, whose `dropEvent` → `_open` already starts the slideshow, as the in-process drop tests show); otherwise an AssertionError, black centre with the launch text still showing
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The entry point adds nothing between the launch viewer and its drop handling, so the earlier drop cycles already deliver this through the shipped command. A mutation check (`dropEvent` returning early) fails it with black centre and the launch text showing, so I kept it as an end-to-end pin with production restored.

## 2026-10-08 21:01 · `src/mediatagger/test_viewer.py::test_dropping_a_file_while_viewing_another_folder_replaces_the_slideshow_with_that_files_folder_at_that_file`
- Behavior: Dropping a file while viewing another folder replaces the slideshow with that file's folder, starting at that file
- Predicted: passes on first run (`dropEvent` → `_open` → `Slideshow.open` already resolves a file to its folder at that file, with no guard on an existing slideshow); otherwise an AssertionError, blue vs yellow
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The behavior came with the earlier drop cycles. A mutation check (drop opens the file's parent folder, starting at its first item) fails the test with green ≠ yellow, so I kept it as a pin with production restored.

## 2026-10-08 20:58 · `src/mediatagger/test_viewer.py::test_dropping_a_folder_while_viewing_another_folder_replaces_the_slideshow_with_the_dropped_folders_at_its_first_item`
- Behavior: Dropping a folder while viewing another folder replaces the slideshow with the dropped folder's, starting at its first item
- Predicted: passes on first run (`dropEvent` → `_open` replaces `self.slideshow` whatever is showing); otherwise an AssertionError, blue vs green
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: `_open` never guards on an existing slideshow, so drop-to-replace shipped with the launch-screen drop cycle. The test advances the viewed folder to blue before dropping. A mutation check (`dropEvent` returning early while a slideshow is showing) fails it with blue ≠ green, so I kept it as a pin with production restored.

## 2026-10-08 20:54 · `src/mediatagger/test_viewer.py::test_dropping_a_file_onto_the_launch_screen_starts_its_folders_slideshow_at_that_file`
- Behavior: Dropping a file onto the launch screen starts its folder's slideshow at that file
- Predicted: passes on first run (`dropEvent` sends the dropped path to `Slideshow.open`, which already resolves a file to its parent folder starting at that file); otherwise an AssertionError, red vs blue
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: The previous cycle's `dropEvent` → `Slideshow.open(path)` already handles files, so no failing test can drive this behavior. The test isn't vacuous: it drops the second image and asserts blue, which a start-at-first-item drop (red) would fail. I kept it as a pin for the behavior instead of rewriting it.

## 2026-10-08 20:24 · `src/mediatagger/test_viewer.py::test_rejecting_the_viewers_own_o_dialog_pointed_at_a_folder_leaves_the_launch_text_showing`
- Behavior: rejecting the viewer's own `o` dialog after `setDirectory(folder)` leaves the "Drop a folder or file here" launch text showing
- Predicted: passes on first run — `_pick_folder`'s `if picker.exec():` guard (added in the accept cycle, 6874ea8) already returns `None` on reject
- Actual: passes on first run
- Type: passed unexpectedly
- Resolution: behavior already shipped as a side effect of the accept cycle; kept the test as a regression guard after a mutation check (dropping the `exec()` guard makes it fail with `assert [] == ['Drop a fold...']`), production restored untouched.

## 2026-10-08 20:13 · `src/mediatagger/test_viewer.py::test_cancelling_the_o_picker_leaves_the_launch_text_showing`
- Behavior: Cancelling the `o` picker leaves the launch screen showing its "Drop a folder or file here" text
- Predicted: passes on first run — `Viewer._open` already returns early on `None`, and the real `_pick_folder` returns `None`
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: the cancel behavior already shipped with the previous green step's `None` guard, so no failing rewrite exists without changing the behavior under test. The test is kept as a guard driven through the real rejected dialog, because the next item (wiring the dialog's choice back) could regress it.

## 2026-10-08 20:03 · `src/mediatagger/test_viewer.py::test_pressing_a_key_other_than_o_on_the_launch_screen_opens_no_folder_picker_and_keeps_the_launch_text`
- Behavior: a key other than `o` (e.g. `x`) on the launch screen opens no folder picker and leaves the launch text showing
- Predicted: passes on first run — the launch-screen branch of `keyPressEvent` already guards `_pick_folder` behind `Key_O` and returns for every other key
- Actual: passed on first run, as predicted
- Type: passed unexpectedly
- Resolution: the behavior was delivered as a side effect of the `o` picker cycle, so this item has nothing left to drive and cannot go red. I kept the test as a regression guard, not a rewrite, and checked it isn't vacuous: temporarily making every key open the picker made it fail (`[QFileDialog] != [None]`), then I restored `viewer.py`.

## 2026-10-08 20:05 · `src/mediatagger/test_viewer.py::test_pressing_o_on_the_launch_screen_opens_a_folder_picker`
- Behavior: Pressing `o` on the launch screen opens a folder picker
- Predicted: AssertionError, `pickers[0]` is None because nothing modal opens
- Actual: ValueError from `qtbot.waitUntil`, because the callback returned a list (`[]`) instead of a bool
- Type: wrong-reason
- Resolution: `waitUntil` only accepts None/True/False. I changed the predicate to `len(pickers) == 1`, and the test now fails for the predicted reason (`isinstance(None, QFileDialog)`).

## 2026-10-08 20:00 · `src/mediatagger/test_viewer.py::test_a_viewer_opened_on_a_folder_shows_its_first_item_and_not_the_launch_text`
- Behavior: Opening the app with a path shows that path's first item, not the "Drop a folder or file here" text
- Predicted: passes on first run, because the previous green step only sets the launch text in the `folder is None` branch
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The previous launch-screen green step already delivered this. A temporary mutation that took the launch branch every time (reverted) made the test fail on `shown_labels(viewer) == []`, so the test isn't vacuous. I kept it as a pin and didn't rewrite it to force a failure.

## 2026-10-08 18:48 · `src/mediatagger/test_main.py::test_running_the_mediatagger_command_on_a_file_opens_the_fullscreen_viewer_on_that_file`
- Behavior: Running the shipped `mediatagger <file>` command opens the fullscreen viewer on that file
- Predicted: passes on first run — `main()` forwards argv[1] to `Viewer` → `Slideshow.open`, which already branches on `path.is_file()`
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: The test isn't vacuous: it opens the middle file of red/blue/green, so if `main` fell back to the folder's first item the centre would be red, not blue. The behavior was already delivered by the earlier "opening a file path" slideshow item plus the `<folder>` command item. Kept the test as a command-level pin and did not rewrite it into an artificial failure.

## 2026-10-08 18:27 · `src/mediatagger/test_viewer.py::test_pressing_space_in_the_viewer_on_an_unsupported_placeholder_followed_by_a_red_image_hides_the_placeholder_and_paints_red`
- Behavior: Pressing `Space` on an "unsupported" placeholder shows the next item
- Predicted: pass (behavior expected to exist already; a right-reason failure would have been AssertionError, placeholder still visible)
- Actual: passed on first run
- Type: passed unexpectedly
- Resolution: `keyPressEvent` already steps the slideshow and `_show_current` recomputes placeholder visibility from `_current_image().isNull()`, so the earlier placeholder cycle delivered this item. The only failing variant (placeholder → video, where the placeholder wrongly stays up because a video's QImage is null) is the next TODO item, so the test was kept as a characterization test rather than rewritten into a different behavior.

## 2026-10-08 18:24 · `src/mediatagger/test_viewer.py::test_a_viewer_opened_on_a_folder_whose_first_item_is_a_decodable_image_shows_that_image_and_no_unsupported_placeholder`
- Behavior: A decodable image shows the image, not the "unsupported" placeholder
- Predicted: passes on first run — `_show_current` already sets the placeholder visible only when `QImage(...).isNull()`
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: the previous green step toggled the placeholder on `isNull()` instead of always showing it, so this behavior arrived with it; no rewrite can make it fail without asserting something false, so the test stays as a pin that catches a regression to an always-visible placeholder

## 2026-10-08 16:53 · `src/mediatagger/test_video.py::test_pressing_enter_toggles_a_video_between_playing_and_paused`
- Behavior: Pressing `Enter` toggles a video between playing and paused
- Predicted: passes on first run — `VideoPlayer.press` ignores the key and toggles pause on any key
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: the `p` green steps toggled pause on any key, so `Enter` already works; no rewrite can make it fail without asserting something false, so the test stays as a pin on `Enter` that will catch it if a later key-dispatch change (e.g. `Space` → next item) drops `Enter`

## 2026-10-08 16:48 · `src/mediatagger/test_video.py::test_a_playing_video_restarts_from_the_beginning_when_it_reaches_the_end`
- Behavior: A playing video restarts from the beginning when it reaches the end
- Predicted: AssertionError — `engine.idle_active` is True because the player goes idle at end of file
- Actual: AssertionError — `engine.path` is None; `idle_active` was still False when `time-pos` turned None
- Type: right-reason mismatch
- Resolution: libmpv unloads the file (path/time-pos go None) before idle-active flips, so reading idle-active right after end-of-file is racy; dropped that assertion and kept `path`/`time_pos` as the loop evidence.

## 2026-10-08 16:35 · `src/mediatagger/test_slideshow.py::test_stepping_from_an_opened_file_moves_relative_to_that_file`
- Behavior: After opening `IMG_2.jpg` (of `IMG_1`–`IMG_3`), `Space` shows `IMG_3.jpg` and `←` twice from there shows `IMG_1.jpg`
- Predicted: passes on first run — `press` locates `self.current` in the folder listing, so stepping is already relative to the opened file
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: the file-open and `←` green steps already compose into this behavior; no rewrite can make it fail without asserting something false, so the test stays as an integration pin over the open→step sequence

## 2026-10-08 16:32 · `src/mediatagger/test_slideshow.py::test_pressing_right_arrow_shows_the_next_item`
- Behavior: Pressing `→` shows the next item
- Predicted: passes on first run — `Slideshow.press` ignores its `key` argument, so any key advances
- Actual: passed (1 passed)
- Type: passed unexpectedly
- Resolution: the Space green step built a key-agnostic `press`, so → already works; no test of this behavior alone can fail, so the test stays as a pin and key discrimination needs to be driven by a separate behavior (e.g. `←` / an unbound key not advancing)

## 2026-10-08 16:25 · `src/mediatagger/test_folder.py::test_macos_litter_is_not_in_the_slideshow`
- Behavior: macOS litter (`._IMG_1.jpg` AppleDouble files, `.DS_Store`) is not in the slideshow
- Predicted: passes, because the hidden-file rule in `_is_media` (leading `.`) already rejects both AppleDouble files and `.DS_Store`
- Actual: passes (1 passed)
- Type: passed unexpectedly
- Resolution: The previous item's hidden-file rule covers this one completely, so no rewrite can make it fail without changing the behavior. I left the test as a guard so the hidden-file rule can't be narrowed in a way that lets macOS litter back in. A later /plan should treat these two TODO items as one.

## 2026-10-08 16:19 · `src/mediatagger/test_folder.py::test_opening_a_folder_lists_its_videos_alongside_its_images_in_natural_order`
- Behavior: Opening a folder lists its videos (`.mp4`, `.mov`, `.avi`, `.mpg`, `.gif`) alongside its images, in the same natural order
- Predicted: passes — the TODO item assumed an image-only listing, but `media_files` returns every file in the folder unfiltered
- Actual: passes (1 passed)
- Type: passed unexpectedly
- Resolution: The previous green step's `folder.iterdir()` was broader than "images", so this behavior already exists. The only way to make it fail is to add a non-media file, which is the next TODO item (`notes.txt`), so I didn't rewrite it. The test stays as a guard so the coming extension filter can't drop videos.
