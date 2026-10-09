# TDD Prediction Mismatches

Append-only audit log of `/red` prediction mismatches and their resolutions. Newest first. Never edit or delete prior entries — that destroys the audit trail.

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
