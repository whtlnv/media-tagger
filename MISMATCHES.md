# TDD Prediction Mismatches

Append-only audit log of `/red` prediction mismatches and their resolutions. Newest first. Never edit or delete prior entries — that destroys the audit trail.

## 2026-10-08 16:19 · `src/mediatagger/test_folder.py::test_opening_a_folder_lists_its_videos_alongside_its_images_in_natural_order`
- Behavior: Opening a folder lists its videos (`.mp4`, `.mov`, `.avi`, `.mpg`, `.gif`) alongside its images, in the same natural order
- Predicted: passes — the TODO item assumed an image-only listing, but `media_files` returns every file in the folder unfiltered
- Actual: passes (1 passed)
- Type: passed unexpectedly
- Resolution: The previous green step's `folder.iterdir()` was broader than "images", so this behavior already exists. The only way to make it fail is to add a non-media file, which is the next TODO item (`notes.txt`), so I didn't rewrite it. The test stays as a guard so the coming extension filter can't drop videos.
