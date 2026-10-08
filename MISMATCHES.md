# TDD Prediction Mismatches

Append-only audit log of `/red` prediction mismatches and their resolutions. Newest first. Never edit or delete prior entries — that destroys the audit trail.

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
