# Backlog

## Out of Scope

- **[src/mediatagger/viewer.py:8] Import cycle between viewer and the package `__init__`** (added: 2026-10-09)
  `mediatagger.viewer → mediatagger → mediatagger.viewer`: viewer imports the package only to read `mediatagger.__file__` in `_never_holds_a_library`, and `main` imports `Viewer`. Transformation broke the suite: test_opening_a_folder_on_the_drive_the_app_runs_from_never_asks_to_create_a_library_writes_nothing_and_says_no_library_viewing_only — `test_viewer_library.app_runs_from` pins the app location by monkeypatching `mediatagger.__file__`, so dropping the edge needs an injected app-location seam instead.

- **[src/mediatagger/test_library.py:17] Schema-version round-trip test compares a class attribute with itself** (added: 2026-10-09)
  `reopened.schema_version == schema_version` always holds because `schema_version` is a `Library` class attribute that `Library.open` never reads from `tags.db`; making the test observe the recorded version through the public API needs `Library.open` to read it back, a production change this pass may not make (the stored value is covered by the meta-table test at line 54).

- **[src/mediatagger/test_main.py:53] Standalone executable test asserts only that the process is still alive** (added: 2026-10-08)
  `assert still_running` checks the process did not exit but not the "viewer open" its name promises; observing the viewer of an independently launched `mediatagger` process needs a production-side report hook, which this pass may not add.

- **[src/mediatagger/library.py:33] `Library.open` and `drive_id` have no production consumer yet** (added: 2026-10-09)
  Phase 3 creates the library and stores its drive id; the viewer discards the `Library` that `create` returns and never opens an existing one. Phase 4 (tagging opens the drive's library) and Phase 6 (backups under `<drive_id>/`) are the intended consumers; until then they are exercised only by `test_library.py`.
