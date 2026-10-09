# TDD Prediction Mismatches

Append-only audit log of `/red` prediction mismatches and their resolutions. Newest first. Never edit or delete prior entries — that destroys the audit trail.

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
