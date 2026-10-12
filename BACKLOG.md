# Backlog

## Out of Scope

- **[src/mediatagger/state.py:17] `remember` keeps the remembered geometry by name, while `remember_geometry` keeps everything** (added: 2026-10-12)
  Each new remembered key must also be carried over by hand in `remember`, or remembering a folder drops it. Unifying both through `_read` would also keep keys the app never wrote, and `remember` would start swallowing write errors as `remember_geometry` does; both are behavior changes a refactor may not make.

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
