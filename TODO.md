# TODO

Note for every cycle: put new tag-prompt and autocomplete viewer tests in `src/mediatagger/test_viewer_tag_prompt.py` (create it if missing; `test_viewer_library.py` is already over 1000 lines). Library-level tests go in `test_library.py`. Tests run offscreen and silent (`player_options={"ao": "null"}`), close every window/popup they open, and never touch real drives or `~`. Widget lifetimes: build the completer and its popup once per viewer, keep a reference on the viewer, and update its model in place; never create a completer, model or popup per keystroke. Garbage is collected only on the GUI thread (`collect_garbage_on_the_gui_thread` in gui_thread_gc.py, called by every Viewer); keep it that way.

Phase 6 notes for every cycle: backup logic lives in a new `src/mediatagger/backup.py` with its tests in `src/mediatagger/test_backup.py`; viewer-level backup/restore tests go in a new `src/mediatagger/test_viewer_backup.py`. Tests never touch the real home folder: pass `backup_root=` (a tmp dir) and a clock seam, and once the viewer starts backing up, `src/mediatagger/conftest.py` must point `XDG_DATA_HOME` at a per-test temp folder (autouse fixture) so the many existing viewer tests that pass no `backup_root=` never write under `~`. Restore questions are injectable (`ask_to_restore_library=`) so no real modal opens. Prefer a synchronous backup (a few-MB tags.db takes well under a second); if a worker thread is ever used, only plain Python and sqlite run in it, results come back via signals, and no Qt object is touched or freed off the GUI thread. A failed backup must never raise out of the viewer. Status messages keep their leading sign exactly as written in the item (`⟳ `, `✓ `, `✗ `). A backup's `<date time>` is always its time in local time as `YYYY-MM-DD HH:MM` (as `RESTORE_LIBRARY_QUESTION` does with `taken_at.astimezone()`). Copies of a database (backup and restore) always go through SQLite's online backup API (`_copy_database` in backup.py), never a file copy.


## Phase 6 — Database backups

- [x] Backing up a library writes a copy of its `tags.db` to `<backup root>/<drive_id>/tags-<UTC time>.db`, named from the given clock (`tags-20261009T153000Z.db`), and opening the copy shows the library's tags
- [x] With `XDG_DATA_HOME` set, the default backup root is `$XDG_DATA_HOME/mediatagger/backups`
- [x] With `XDG_DATA_HOME` unset, the default backup root is `~/.local/share/mediatagger/backups` (the test points `HOME` at a temp folder)
- [x] Backing up writes `drive.json` next to the drive's backups, recording the drive's name (its mount point's folder name) and its drive id
- [x] Backing up a drive that already has 10 backups leaves only the 10 newest, the oldest deleted
- [x] Backing up a drive that has fewer than 10 backups deletes none of them
- [x] Backing up a library whose database hasn't changed since that drive's last backup writes no new backup
- [x] Backing up a library whose tags changed since that drive's last backup writes a new backup
- [x] Backing up a library tagged `beach`, then entering `sunset` on the same item and backing up again at the same clock second, leaves a backup holding `beach` and `sunset` (the new copy is never deleted as a duplicate of the backup it replaced)
- [x] Backing up into a backup root that isn't writable reports a failure with a short reason instead of raising
- [x] For a drive name with backups, the newest backup and its date and time are found by matching `drive.json` names
- [x] For a drive name with no backups, no backup is found
- [x] Restoring a drive from a backup keeps the damaged file as `.mediatagger/tags.db.damaged-<timestamp>` and replaces `tags.db` with the backup, so the library opens with the backed-up tags
- [x] Opening a folder on a drive whose library opens backs up that drive's database into the viewer's backup root (`backup_root=`)
- [x] Opening a folder on a drive whose library can't be opened makes no backup
- [x] Closing the viewer after tagging an item leaves a backup containing that tag, written before the close returns
- [x] Opening a folder on another drive after tagging an item leaves a backup of the first drive containing that tag
- [x] While a backup is running, the status bar shows `⟳ Backing up database…`
- [x] When a backup finishes, the status bar shows `✓ Backed up`
- [x] On a shown viewer, the status bar message while backing up reads exactly `⟳ Backing up database…` (with its ⟳ sign), the message once it finishes reads exactly `✓ Backed up` (with its ✓ sign), and the backing-up message has already been painted on screen when the copy starts (the label received a paint event before the backup ran, since the backup is synchronous)
- [x] A few seconds after a backup finishes, `✓ Backed up` is cleared from the status bar
- [x] When a backup fails because the backup root isn't writable, the status bar shows `✗ Backup failed: <short reason>` and the viewer keeps showing the item
- [x] When a backup fails, tagging the current item still saves its tags
- [x] Backing up a library whose `tags.db` was overwritten with garbage after it opened reports a failure with a short reason instead of raising, and leaves no new file in the drive's backup folder (a half-written copy must never become the newest backup)
- [x] When writing a drive's `drive.json` fails during a backup (e.g. a folder already sits at that path), the viewer shows `✗ Backup failed: <short reason>` and keeps showing the item — no `OSError` or `sqlite3.Error` from a backup ever escapes the viewer
- [x] Opening a folder on a drive whose `tags.db` is garbage, with backups for a drive of the same name, asks "The tag library on <DRIVE> is missing or damaged. Restore the backup from <date time>?" (`ask_to_restore_library=`)
- [x] A viewer given no `backup_root=` finds restore backups under the default backup root (`$XDG_DATA_HOME/mediatagger/backups`), so opening a drive whose `tags.db` is garbage, with a backup there for a drive of the same name, asks the restore question
- [x] The restore question shows the backup's time in local time as `YYYY-MM-DD HH:MM` (e.g. a backup taken at 15:30 UTC reads `2026-10-09 09:30` with the local zone at UTC−6)
- [x] Opening a folder on a drive whose `tags.db` is garbage, with no backups for a drive of that name, asks nothing and shows `Library on <DRIVE> can't be opened — viewing only`
- [x] Answering Yes to the restore question opens the library with the backed-up tags shown for the current item and the status bar showing `✓ Restored backup from <date time>`
  - the test asserts the literal text, not an imported constant: with the local zone at UTC−6 (`local_time_zone("America/Mexico_City")` in test_viewer_backup.py) and a backup taken at 2026-10-09 15:30 UTC, the status bar shows exactly `✓ Restored backup from 2026-10-09 09:30`
- [x] Answering No to the restore question for a garbage `tags.db` shows `Library on <DRIVE> can't be opened — viewing only`
- [x] Opening a folder on a drive whose `.mediatagger/` exists without `tags.db`, with backups for a drive of the same name, asks the restore question
- [x] Answering No to the restore question for a missing `tags.db` asks the create-library question
- [x] Answering Yes to the restore question for a missing `tags.db` (`.mediatagger/` exists) opens the library with the backed-up tags shown for the current item and the status bar showing `✓ Restored backup from <date time>`
- [x] Answering Yes to the restore question when the newest backup is itself unreadable (garbage bytes) shows `✗ Restore failed: <short reason>` and `Library on <DRIVE> can't be opened — viewing only`, never raises, and leaves the drive's original damaged `tags.db` back in place as `tags.db`
- [ ] Opening a folder on a read-only drive whose `tags.db` is garbage, with backups for a drive of the same name, asks no restore question and the status bar says the backup can't be restored to a read-only drive, viewing only
- [ ] Running the shipped `mediatagger <folder>` on a drive whose `tags.db` is garbage, with a backup for a drive of that name under `$XDG_DATA_HOME`, asks the restore question in a Yes/No dialog over the already shown viewer (the default `ask_to_restore_library`), and answering Yes shows the restored tags
- [ ] Running the shipped `mediatagger <folder>` with `XDG_DATA_HOME` pointing at a temp folder, on a drive with a library, leaves a backup of that drive's database under `$XDG_DATA_HOME/mediatagger/backups/<drive_id>/` after the viewer closes
