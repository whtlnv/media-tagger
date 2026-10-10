# Backlog

## Out of Scope

- **[src/mediatagger/folder.py:39] The video and media extension rules are defined twice, once on Paths and once on names** (added: 2026-10-10)
  `is_video`/`_has_media_extension` use `Path.suffix` while `is_video_name` and `subfolder_and_media_names` use `os.path.splitext`; unifying them changes how a name such as `..mp4` is classified (`Path.suffix` gives `.mp4`, `splitext` gives none), a behavior change a refactor may not make.

- **[src/mediatagger/test_viewer_backup.py:394] Test monkeypatches the private `viewer._FINISHED_MESSAGE_MS`** (added: 2026-10-10)
  The backup-failure-outlives-earlier-message test shortens the private clear delay through `viewer_module`; `Viewer` offers no public way to set how long a finished background message stays, so decoupling needs a production change (e.g. a constructor option).

- **[src/mediatagger/viewer.py:419] `Viewer` is a 436-line class that also owns the library open/restore/backup flow** (added: 2026-10-10; location corrected 2026-10-10)
  `_open_library` through `_agrees_to_create_library` (~100 lines) decide what to do with a drive's library and write the status bar, banner and background-status widgets directly; moving them out means designing a new boundary between that decision and the widgets, an architectural split for `/complexity-pass`, not a mechanical refactor.

- **[src/mediatagger/backup.py:58] `back_up` reads `Library._tags_db` and undoes `tags_db_path`'s layout with `.parent.parent`** (added: 2026-10-10)
  The drive name written to `drive.json` depends on `.mediatagger/tags.db` staying exactly two levels below the drive root, a fact `library.tags_db_path` owns; the fix is for `Library` to expose its drive root (and database path) publicly, which needs a change in `library.py`, outside the e41159b..HEAD range.

- **[src/mediatagger/test_main.py:53] Standalone executable test asserts only that the process is still alive** (added: 2026-10-08)
  `assert still_running` checks the process did not exit but not the "viewer open" its name promises; observing the viewer of an independently launched `mediatagger` process needs a production-side report hook, which this pass may not add.
