# TDD Prediction Mismatches

Append-only audit log of `/red` prediction mismatches and their resolutions. Newest first. Never edit or delete prior entries — that destroys the audit trail.

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
