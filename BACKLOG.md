# Backlog

## Out of Scope

- **[src/mediatagger/test_window.py] The 854-line window test file still mixes navigation, grid tagging and backup tests** (added: 2026-10-14)
  The grid tag-prompt cluster (`test_pressing_t_in_the_windows_grid_…` through the prompt-placement test) could move to its own `test_window_tags.py`, but its helpers `window_showing_the_grid_with_its_cursor_on_its_first_tile`, `enter_in_the_grids_tag_prompt` and `shown_status_bar_texts` are imported by `test_search_bar.py` and `test_window_search_opening_results.py`, outside the ca048de..HEAD range, so moving the cluster with them needs edits there.

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

- **[src/mediatagger/test_video_controls.py:186] The `↑`-on-hidden-bar seek test fails under machine load** (added: 2026-10-13)
  `test_up_on_a_playing_video_whose_progress_bar_is_hidden_shows_the_bar_at_once_at_the_new_position` read `0:00 / 1:05` instead of `0:10 / 1:05` several times during Phase 11 while another project's test suite ran on the Mac; it passes on an idle machine. It reads mpv's position right after the seek; waiting for the seek to land (as other video tests do) would remove the timing dependence.

- **[drive/build-drive.sh] The drive's `debs/` holds libmpv2's whole dependency closure, not only what the Pi lacks** (added: 2026-10-13)
  `~/aptpi` in the VM is an apt root with an empty dpkg status, so its archive holds 389 `.deb`s (~255 MB) and `build-drive.sh` copies them all; apt on the Pi installs only the missing ones (6 on the 2026-10-08 run). Trimming needs the Pi's package list (e.g. a `dpkg --get-selections` copied from the Pi into the Pi-like apt root's status) — only worth it if stick space matters.

- **[drive/update-drive.sh] Bytecode on the drive records the path it was compiled at** (added: 2026-10-13)
  `compileall` runs against `/Volumes/MEDIATAGGER/...` (Mac) or the VM's path, so tracebacks on the Pi name that path instead of `/media/<user>/MEDIATAGGER/...`; behaviour is unaffected (unchecked-hash pycs are never revalidated). `compileall -s <drive> -p /media/<user>/MEDIATAGGER` would fix it if the mount path is fixed.
