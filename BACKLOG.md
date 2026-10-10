# Backlog

## Out of Scope

- **[src/mediatagger/viewer.py:419] `Viewer` is a 560-line class that also owns the library open/restore/backup flow** (added: 2026-10-10)
  `_open_library` through `_agrees_to_create_library` (~100 lines) decide what to do with a drive's library and write the status bar, banner and background-status widgets directly; moving them out means designing a new boundary between that decision and the widgets, an architectural split for `/complexity-pass`, not a mechanical refactor.

- **[src/mediatagger/backup.py:58] `back_up` reads `Library._tags_db` and undoes `tags_db_path`'s layout with `.parent.parent`** (added: 2026-10-10)
  The drive name written to `drive.json` depends on `.mediatagger/tags.db` staying exactly two levels below the drive root, a fact `library.tags_db_path` owns; the fix is for `Library` to expose its drive root (and database path) publicly, which needs a change in `library.py`, outside the e41159b..HEAD range.

- **[src/mediatagger/test_main.py:53] Standalone executable test asserts only that the process is still alive** (added: 2026-10-08)
  `assert still_running` checks the process did not exit but not the "viewer open" its name promises; observing the viewer of an independently launched `mediatagger` process needs a production-side report hook, which this pass may not add.

- **[src/mediatagger/library.py:60] `Library.drive_id` has no production consumer yet** (added: 2026-10-09; rescoped 2026-10-09; location corrected 2026-10-09)
  The library stores its drive id, but nothing outside the tests (`test_library.py`, `test_viewer_library.py`) reads it — the viewer now keeps the `Library` it creates or opens (`viewer.py:412-415`) yet never uses `drive_id`. Phase 6 (backups under `<drive_id>/`) is the intended consumer; until then it is exercised only by `test_library.py` and `test_viewer_library.py`.
