# Backlog

## Out of Scope

- **[src/mediatagger/test_main.py:53] Standalone executable test asserts only that the process is still alive** (added: 2026-10-08)
  `assert still_running` checks the process did not exit but not the "viewer open" its name promises; observing the viewer of an independently launched `mediatagger` process needs a production-side report hook, which this pass may not add.

- **[src/mediatagger/library.py:60] `Library.drive_id` has no production consumer yet** (added: 2026-10-09; rescoped 2026-10-09; location corrected 2026-10-09)
  The library stores its drive id, but nothing outside the tests (`test_library.py`, `test_viewer_library.py`) reads it — the viewer now keeps the `Library` it creates or opens (`viewer.py:412-415`) yet never uses `drive_id`. Phase 6 (backups under `<drive_id>/`) is the intended consumer; until then it is exercised only by `test_library.py` and `test_viewer_library.py`.
