# Backlog

## Out of Scope

- **[src/mediatagger/folder.py:39] The video and media extension rules are defined twice, once on Paths and once on names** (added: 2026-10-10)
  `is_video`/`_has_media_extension` use `Path.suffix` while `is_video_name` and `subfolder_and_media_names` use `os.path.splitext`; unifying them changes how a name such as `..mp4` is classified (`Path.suffix` gives `.mp4`, `splitext` gives none), a behavior change a refactor may not make.

- **[src/mediatagger/test_viewer_backup.py:393] Test monkeypatches the private `status_bar._FINISHED_MESSAGE_MS`** (added: 2026-10-10; location corrected 2026-10-10)
  The backup-failure-outlives-earlier-message test shortens the private clear delay through `status_bar_module`; `StatusBar` offers no public way to set how long a finished background message stays, so decoupling needs a production change (e.g. a constructor option).

- **[src/mediatagger/backup.py:51] `_back_up` reads the private `Library._tags_db`** (added: 2026-10-10; rescoped 2026-10-10)
  The database copy goes through `library._tags_db`, the path `library.tags_db_path` lays out; the fix is for `Library` to expose its database path publicly (as it now does its drive root through `Library.root`), which needs a change in `library.py`, outside the e41159b..HEAD range.

- **[src/mediatagger/test_main.py:53] Standalone executable test asserts only that the process is still alive** (added: 2026-10-08)
  `assert still_running` checks the process did not exit but not the "viewer open" its name promises; observing the viewer of an independently launched `mediatagger` process needs a production-side report hook, which this pass may not add.
