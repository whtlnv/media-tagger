# Backlog

## Out of Scope

- **[src/mediatagger/test_window_search.py:487] Test imports test_library's private `_create_schema_version_1_library` and `_read_only_drive`** (added: 2026-10-16)
  The read-only schema-version-1 search test reaches two private helpers of `test_library.py`; no public equivalent exists (`made_read_only` locks only the drive root, not `.mediatagger` and `tags.db`, so the upgrade would still write), and making them public needs a rename in `test_library.py`, outside the 29bbecd..HEAD range.

- **[src/mediatagger/rename_prompt.py:_RecallingInput] The rename input's ↑/↓ recall repeats the search bar's** (added: 2026-10-16)
  `_RecallingInput.keyPressEvent` re-implements `SearchBar.recall_older_search`/`recall_newer_search` (step back through a remembered list, empty past the newest) over `remembered_renames` instead of `remembered_searches`. Unifying them needs a new shared recall helper that `search_bar.py`, outside the 29bbecd..HEAD range, would adopt; hoist it when the search bar is next touched.

- **[src/mediatagger/chapters.py:Chapters] Chapters reaches into six of the viewer's attributes** (added: 2026-10-15)
  To stay out of `viewer.py` (at its 270-line budget) `Chapters` filters the viewer's keys and uses its `slideshow`, `session`, `status_bar`, `tag_prompt`, `video_player` and `progress_bar` directly, and the viewer calls `chapters.read` from `_show_tag_overlay` so moments are re-read whenever tags are. A narrower seam (the viewer handing Chapters the current item, library and player) would decouple them, but needs room in `viewer.py`.

- **[src/mediatagger/library.py:_set_item_tags] Moments an older build leaves behind stay in `tags.db` until that video's tags are next saved** (added: 2026-10-15)
  A build from before Phase 18 run on a schema-3 drive removes a tag without its `moments` rows. Reads join through `item_tags`, so those rows never show, and the next save of that video's tags in this build deletes them before anything is added (so a tag added back never revives them). Only a few stray rows on disk; a sweep on open would remove them sooner, at the cost of a write on every open.

- **[src/mediatagger/zoom.py:37] A zoom's pan is clamped only when the wheel turns, not when the window resizes or `r` turns a video** (added: 2026-10-15)
  `Zoom.pan` is kept in fractions of the shown picture, so a zoom survives `f`/a resize/`r` centred where it was, but the no-black-edge clamp in `Zoom.wheel` is not re-run against the new fitted rect until the next wheel turn, so a zoomed picture panned to an edge can show black there after a resize or a turn. Fixing it needs the viewer to re-clamp on resize and on `r` (a `Zoom.reclamp(fitted, window)` called from `resizeEvent` and the `r` key), lines `viewer.py` has no room for under its 270-line budget.

- **[src/mediatagger/viewer.py:239] Zooming a photo decodes it at up to 3x the window** (added: 2026-10-15)
  `Zoom.detail()` makes `_current_image` decode once more, no larger than three times the window (and never larger than the photo), on the first notch past 100 %. On a 2560x1080 screen that is a 12 MP photo decoded whole (~48 MB of RGB32), one extra full decode; unmeasured on the Pi. If it lags there, decode at the window size times the current level only after the wheel settles.

- **[src/mediatagger/test_video_controls.py:335] Window staging (`Window(…, player_options=SILENT)`, `addWidget`, `show_exposed`) is repeated with no shared helper** (added: 2026-10-14; location corrected 2026-10-14; location corrected 2026-10-16; location corrected 2026-10-16)
  This file now repeats it five times, but the same three lines show up 37 times in total, mostly in test files outside 76e644f..HEAD. A helper beside `show_exposed` in `test_viewer.py` would only be partly adopted if this range's sites used it alone. Hoist it when those other files are touched.

- **[src/mediatagger/test_window.py] The 896-line window test file still mixes navigation, grid tagging and backup tests** (added: 2026-10-14; location corrected 2026-10-14; location corrected 2026-10-15; location corrected 2026-10-15; location corrected 2026-10-15; location corrected 2026-10-16)
  The grid tag-prompt cluster (`test_pressing_t_in_the_windows_grid_…` through the prompt-placement test) could move to its own `test_window_tags.py`, but its helpers `window_showing_the_grid_with_its_cursor_on_its_first_tile`, `enter_in_the_grids_tag_prompt` and `shown_status_bar_texts` are imported by `test_search_bar.py`, `test_window_cheat_sheet.py`, `test_window_grid_filter.py`, `test_window_rename.py`, `test_window_required_tags.py`, `test_window_search.py`, `test_window_search_opening_results.py`, `test_window_state.py` and `test_window_thumbnails.py`, outside the ca048de..HEAD range, so moving the cluster with them needs edits there.

- **[src/mediatagger/folder.py:39] The video and media extension rules are defined twice, once on Paths and once on names** (added: 2026-10-10)
  `is_video`/`_has_media_extension` use `Path.suffix` while `is_video_name` and `subfolder_and_media_names` use `os.path.splitext`; unifying them changes how a name such as `..mp4` is classified (`Path.suffix` gives `.mp4`, `splitext` gives none), a behavior change a refactor may not make.

- **[src/mediatagger/test_viewer_backup.py:393] Test monkeypatches the private `status_bar._FINISHED_MESSAGE_MS`** (added: 2026-10-10; location corrected 2026-10-10)
  The backup-failure-outlives-earlier-message test shortens the private clear delay through `status_bar_module`; `StatusBar` offers no public way to set how long a finished background message stays, so decoupling needs a production change (e.g. a constructor option).

- **[src/mediatagger/backup.py:51] `_back_up` reads the private `Library._tags_db`** (added: 2026-10-10; rescoped 2026-10-10)
  The database copy goes through `library._tags_db`, the path `library.tags_db_path` lays out; the fix is for `Library` to expose its database path publicly (as it now does its drive root through `Library.root`), which needs a change in `library.py`, outside the e41159b..HEAD range.

- **[src/mediatagger/test_main.py:53] Standalone executable test asserts only that the process is still alive** (added: 2026-10-08)
  `assert still_running` checks the process did not exit but not the "viewer open" its name promises; observing the viewer of an independently launched `mediatagger` process needs a production-side report hook, which this pass may not add.

- **[src/mediatagger/thumbnail_cache.py:generate_through_cache] A video whose frame fails is stored as a plain failure, losing its duration** (added: 2026-10-11)
  When `ffprobe` gives a duration but `ffmpeg` gives no frame, `store_failure` records no duration, so the tile shows ▶ without a duration until the file changes. Keeping it needs `store_failure` to take a duration (a schema-compatible column already exists).

- **[src/mediatagger/folder_thumbnails.py:FolderThumbnails.start] Every folder open stats every file on a worker for the cache survey** (added: 2026-10-11)
  `still_to_generate` stats each file of the folder to compare size and mtime; on a USB stick on a Pi a folder of thousands may take a while before `⟳ Generating thumbnails` shows its total. Measure on the Pi before optimising (e.g. trusting the folder's mtime).

- **[src/mediatagger/grid.py:HELD_THUMBNAILS] Pictures are held at the largest tile size whatever the zoom** (added: 2026-10-11)
  Each held picture is up to 400×400 RGB32 (~0.5 MB); with 500 held plus the tiles in view, memory can reach ~250–300 MB. Scaling held pictures to the current tile size (re-requesting on zoom-in) would cut that on the Pi.

- **[src/mediatagger/test_grid.py] The 5,000-file timing tests depend on collecting garbage first** (added: 2026-10-11)
  Inside the full suite a garbage collection during the timed opening pushed it past 150 ms; `fastest_of_three` now collects before each opening. In the app the GUI-thread GC timer can still fire mid-open; if opening feels slow on the Pi, look there first.

- **[src/mediatagger/window.py:Window._show_results] Back from a results slideshow, the results grid's thumbnails stay stopped** (added: 2026-10-13)
  Opening a result file stops the results grid's thumbnail workers (as for a folder grid), but `Esc` returns to the same results grid instead of building a new one, so tiles whose thumbnails had not arrived keep their glyph until the next search. Restarting generation on return (or rebuilding the results grid) would fix it.

- **[src/mediatagger/grid.py:_result_kind] Each result stats its path twice when the results grid opens** (added: 2026-10-13)
  `exists()` then `is_dir()` per result; 5,000 results open in ~80 ms on the Mac. On a Pi's USB stick this may be several times slower; one `os.stat` per path (or trusting the library's recorded kind for folders) would halve it. Measure on the Pi first.

- **[src/mediatagger/test_video_controls.py:197] The `↑`-on-hidden-bar seek test fails under machine load** (added: 2026-10-13; location corrected 2026-10-14)
  The `up shows the bar at the new position` case of `test_a_key_on_a_playing_video_whose_progress_bar_is_hidden_shows_the_bar_at_once_reading_any_change` read `0:00 / 1:05` instead of `0:10 / 1:05` several times during Phase 11 while another project's test suite ran on the Mac; it passes on an idle machine. It reads mpv's position right after the seek; waiting for the seek to land (as other video tests do) would remove the timing dependence.

- **[drive/build-drive.sh] The drive's `debs/` holds libmpv2's whole dependency closure, not only what the Pi lacks** (added: 2026-10-13)
  `~/aptpi` in the VM is an apt root with an empty dpkg status, so its archive holds 389 `.deb`s (~255 MB) and `build-drive.sh` copies them all; apt on the Pi installs only the missing ones (6 on the 2026-10-08 run). Trimming needs the Pi's package list (e.g. a `dpkg --get-selections` copied from the Pi into the Pi-like apt root's status) — only worth it if stick space matters.

- **[drive/update-drive.sh] Bytecode on the drive records the path it was compiled at** (added: 2026-10-13)
  `compileall` runs against `/Volumes/MEDIATAGGER/...` (Mac) or the VM's path, so tracebacks on the Pi name that path instead of `/media/<user>/MEDIATAGGER/...`; behaviour is unaffected (unchecked-hash pycs are never revalidated). `compileall -s <drive> -p /media/<user>/MEDIATAGGER` would fix it if the mount path is fixed.

- **[src/mediatagger/thumbnail_scheduler.py:_Work.run] Quitting still waits for each worker's file in progress** (added: 2026-10-14)
  Closing the window now stops every grid's generation (Phase 12), so the process ends after at most the files the 3 workers are on. Each is bounded by `TOOL_TIMEOUT_S` (15 s) per `ffprobe`/`ffmpeg` call, so a hung tool on a slow stick could still hold the exit for up to ~30 s. Killing the running tool subprocesses on shut-down would remove that; measure on the Pi first.

- **[drive/test_run.py, src/mediatagger/test_main.py] Subprocess timing tests fail under machine load** (added: 2026-10-14)
  During Phase 12, with another project's suite running (load 10–18), `test_run_with_a_real_python3_starts_the_real_app_from_the_drive_app_and_the_drive_gains_no_files` (8 s to reach `window.pyc`) failed several times, and the 3 s quit tests and `test_zero_on_a_playing_video_seeks_back_to_the_start` failed once each; all pass on rerun and on an idle machine. More slack, or waiting on a printed marker instead of a fixed time, would stop them blocking unattended commits.

- **[src/mediatagger/grid.py:Grid.show_new_tags] Every tag save re-reads the whole grid's tag counts and marks** (added: 2026-10-15; description corrected 2026-10-15)
  So that a change one item's tags make to what others inherit shows at once, each save from the tag prompt re-reads the shown folder's tag counts, moment counts, own tags and inherited tags (four bulk queries), or for results every tagged item; with required roots a 5,000-file folder opens in ~70 ms on the Mac against ~60 ms without them. Unmeasured on the Pi; if saving a tag lags there in a big folder, update only the saved item's tile when it is a file.

- **[src/mediatagger/window.py:Window._open_tile] A slideshow opened from a filtered grid (or from results) drops the info overlay's state** (added: 2026-10-15)
  `viewer.open(path)` builds the folder's slideshow (carrying `i`'s overlay over), then the window replaces it with `Slideshow(shown, …)`, whose overlay starts off — so with `i` on, opening a file from a filtered grid or from results shows no filename/position until `i` is pressed again (results did this before Phase 17). Passing the files to `Viewer.open` instead would fix it, but `viewer.py` is at its 270-line budget.

- **[src/mediatagger/folder_thumbnails.py:FolderThumbnails.start] Background prefetch still generates thumbnails for files a filter hides** (added: 2026-10-15)
  A filtered grid never asks for a hidden tile's thumbnail, but the prefetch of the rest of the folder still generates them, so on the Pi a filtered big folder does the same background work as an unfiltered one. Harmless (they are cached for when the filter goes off); skip hidden files in the prefetch if it matters there.
