# Backlog

## Out of Scope

- **[src/mediatagger/test_main.py:53] Standalone executable test asserts only that the process is still alive** (added: 2026-10-08)
  `assert still_running` checks the process did not exit but not the "viewer open" its name promises; observing the viewer of an independently launched `mediatagger` process needs a production-side report hook, which this pass may not add.

- **[src/mediatagger/library.py:33] `Library.open` and `drive_id` have no production consumer yet** (added: 2026-10-09)
  Phase 3 creates the library and stores its drive id; the viewer discards the `Library` that `create` returns and never opens an existing one. Phase 4 (tagging opens the drive's library) and Phase 6 (backups under `<drive_id>/`) are the intended consumers; until then they are exercised only by `test_library.py`.
