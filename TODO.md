# TODO

Phase 8 notes for every cycle. Architecture: `viewer.py` must not grow, and `grid.py` stays the view/model/delegate only. Thumbnail generation (Qt image decode, `ffmpeg` frame, `ffprobe` duration, folder first-image lookup) lives in a new `src/mediatagger/thumbnails.py` with tests in `src/mediatagger/test_thumbnails.py`; the on-disk cache (`thumbs.db` under `$XDG_CACHE_HOME/mediatagger/<drive_id>/`) in a new `src/mediatagger/thumbnail_cache.py` with `src/mediatagger/test_thumbnail_cache.py`; the scheduler (3 workers, newest request first, then background prefetch of the rest of the folder, cancel on leaving a folder) may live with generation or in its own module, but never in `grid.py` or `window.py`. The grid's `_Tile` gains the thumbnail/duration slot left for it in Phase 7; the delegate keeps painting from `TILE_ROLE` only and never stats, decodes or queries. Workers never create or touch widgets; results reach the model on the GUI thread via signals (queued connections). `gui_thread_gc` stays in force — no code may re-enable automatic GC, and worker threads must not hold the last reference to Qt objects. Subprocesses (`ffmpeg`, `ffprobe`) always run with a timeout, and their absence (not on PATH) is a handled case with a test using an injectable seam — never by uninstalling or renaming real binaries. Test media is made in temp dirs (Qt-written images; tiny videos made with `ffmpeg` in a fixture, skipped if `ffmpeg` is missing). Before the first test whose code path writes `thumbs.db`, `src/mediatagger/conftest.py` must point `XDG_CACHE_HOME` at a per-test temp folder (autouse, exactly like `backups_never_reach_the_real_home_folder` and `state_never_reaches_the_real_home_folder`) so no test ever writes the real `~/.cache`. Tests run offscreen and silent (`player_options={"ao": "null"}`), close every window they open, wait for background work deterministically (signals / `QTest.qWaitFor`, never bare sleeps), and never touch real drives or `~`: use temp dirs and the existing seams (`is_mount_point=`, `app_location=`, `ask_to_create_library=`, `ask_to_restore_library=`, `backup_root=`, config home). Create mpv players only via `video.new_engine()`. The existing 5,000-file grid timing test must keep passing. No cycle opens on-screen windows or takes screenshots of the real display; the orchestrator does native verification itself. Never write to `/Volumes/MEDIATAGGER` and never touch `spikes/`.


## Phase 8 — Thumbnails

### Generating one thumbnail
- [x] A 1600×800 image yields a thumbnail of 400×200 (fits ~400 px, aspect ratio kept)
- [x] A 300×600 image yields a thumbnail of 200×400 (the long side, not always the width, is fitted)
- [x] An image whose EXIF orientation says "rotated 90°" yields a thumbnail in its displayed (rotated) orientation
- [x] A corrupt image file yields a "no thumbnail" result instead of raising
- [x] A video yields its duration in seconds
- [x] A video yields a frame taken at ~10% of its duration, not its first frame (a test video whose colour changes after the first 5% gives the later colour)
- [x] A video's frame thumbnail fits within ~400 px, aspect ratio kept
- [x] When `ffmpeg`/`ffprobe` are not on PATH, a video yields "no thumbnail" and no duration instead of raising
- [x] A 7-second video yields a duration of about 7 s (read from the file with `ffprobe`, not assumed)
- [x] An 800×600 video that is green at 10% of its length yields a green 400×300 thumbnail (the frame is taken from the file with `ffmpeg`, not made up)
- [x] When `ffmpeg` runs past its timeout, the video yields "no thumbnail" and generation returns promptly
- [x] A corrupt video file yields "no thumbnail" and no duration instead of raising
- [x] A folder whose images are `10.jpg` and `2.jpg` yields the thumbnail of `2.jpg` (first image in natural order)
- [x] A folder holding only videos, or images only in its subfolders, yields "no thumbnail"
- [x] A duration of 75 s reads `1:15`
- [x] A duration of 3,725 s reads `1:02:05` (hours shown from an hour)
- [x] A fractional duration of 75.6 s, as `ffprobe` reports it, reads `1:15` (whole seconds only)
- [x] When `ffprobe` runs past its timeout, the video yields no duration and no thumbnail and generation returns promptly

### Cache
- [x] Tests that write a thumbnail cache write it under a per-test temp folder, never the real `~/.cache`
- [x] With `$XDG_CACHE_HOME` set, a drive's cache is `$XDG_CACHE_HOME/mediatagger/<drive_id>/thumbs.db`
- [x] With `$XDG_CACHE_HOME` unset, a drive's cache is `~/.cache/mediatagger/<drive_id>/thumbs.db` (home injectable)
- [x] A stored thumbnail is returned for a file whose size and mtime are unchanged
- [x] A stored thumbnail is not returned once the file's mtime changes
- [x] A stored thumbnail is not returned once the file's size changes
- [x] Thumbnails stored for two different files are each returned for their own file
- [x] A stored video thumbnail comes back with its duration
- [ ] A stored failure comes back as a hit meaning "no thumbnail", distinguishable from a miss (which stays as it is today), while the file is unchanged
- [ ] A stored failure is a miss once the file's mtime changes
- [ ] Thumbnails stored in one session are returned after the cache is reopened (survives restarting the app)
- [ ] A thumbnail stored while the drive was mounted at one path is returned when the drive is mounted at another
- [ ] With no drive id (no library), a generated thumbnail is returned again within the session from memory
- [ ] With no drive id, nothing is written to disk
- [ ] The cache is never written when its location falls on the app's own drive
- [ ] The cache is never written when its location falls on the drive being viewed

### Order of work
- [ ] With more than three thumbnails pending, exactly three generate at once
- [ ] While workers are busy, the most recently requested thumbnail is generated before earlier pending ones
- [ ] Re-requesting a thumbnail that is already pending moves it ahead of the others
- [ ] Once the requested thumbnails are done, the rest of the folder's thumbnails are generated without being requested
- [ ] A thumbnail requested while the rest of the folder is prefetching is generated before the remaining prefetch
- [ ] Leaving a folder drops its pending thumbnails: they are never generated
- [ ] A thumbnail already generating when its folder is left still finishes and is cached
- [ ] Generated thumbnails are delivered on the GUI thread
- [ ] Requesting thumbnails that are all cached generates nothing

### Grid
- [ ] In a folder's grid, an image tile gets its thumbnail once generation finishes
- [ ] In a folder's grid, a corrupt image's tile keeps no thumbnail (its glyph stays)
- [ ] In a folder's grid, a video tile gets its thumbnail and its duration
- [ ] In a folder's grid, a folder tile gets the thumbnail of its first image
- [ ] In a folder's grid, a folder tile with no image directly inside keeps no thumbnail
- [ ] In a large folder's grid, tiles in view get their thumbnails before tiles far out of view
- [ ] Scrolling a large folder's grid makes the newly visible tiles' thumbnails arrive before still-hidden ones
- [ ] A thumbnail arriving reports a change for its own tile's row only
- [ ] Entering a subfolder, going up, or starting a slideshow stops generating the left folder's pending thumbnails
- [ ] Opening a folder's grid a second time generates nothing
- [ ] On a drive with a library, the grid's thumbnails are written to that drive's cache
- [ ] On the system disk (no library), the grid's thumbnails are written nowhere on disk
- [ ] Opening the grid of a 5,000-file folder with an empty cache stays within the Phase 7 timing bound

### Painting
- [ ] A tile with a thumbnail paints the picture above the filename, aspect ratio kept
- [ ] A tile without a thumbnail paints its type glyph
- [ ] A video tile paints its duration next to the ▶ badge
- [ ] An image tile paints no duration
- [ ] The tag-count, ▶ and duration badges are painted on a contrasting backing, readable over both a white and a black thumbnail
- [ ] Painting a tile that has a thumbnail stats, decodes and queries nothing

### Status bar
- [ ] While thumbnails generate, the status bar shows `⟳ Generating thumbnails <done> / <total>`, counting only the ones that had to be generated
- [ ] A total of 1,204 reads `1,204` (thousands separated)
- [ ] When the folder's thumbnails are done, the status bar shows `✓ Thumbnails ready`, then clears it like other finished background messages
- [ ] Opening a folder whose thumbnails are all cached shows no thumbnail message

### Shipped
- [ ] The shipped `mediatagger` command's grid (launch on a folder, `Esc` to the grid) shows a generated thumbnail on an image tile
