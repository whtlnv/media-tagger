# MediaTagger — Plan

Delivery phases, in order. Decisions, key maps and rules live in `DESIGN.md`; every phase follows it.
Each phase must end with its behavior reachable from the shipped `mediatagger` command, not only from tests.


Phases 1–28 are delivered. Their specs are in git history (`PLAN.md` at `fcd5d3b` for 1–11, at `ca048de` for 12, at `76e644f` for 13, at `5ba4a0a` for 14, at `9a27389` for 15, at `213f913` for 16, at `f1a53c2` for 17, at `4cc0f4e` for 18, at `a2d1a4e` for 19, at `65d51a2` for 20, at `37d3379` for 21, at `37d3379` for 22, at `37d3379` for 23, at `cc98ca5` for 24, at `cc98ca5` for 25, at `cc98ca5` for 26, at `cc98ca5` for 27, at `cc98ca5` for 28) and their items in `DONE.md`.

## Phase 29 — Del deletes a picture or video from the grid

From the user (2026-10-17): "allow the Del key to delete an image, video or directory from the grid view, please include a confirmation dialog that we can accept with enter and reject with esc". The user decided: deleting is **for good** (no trash, no hidden folder); a folder is deleted with everything in it (Phase 30).

- In a folder grid, `Del` on an image or video tile asks `Delete "IMG_0001.jpg"? It can't be undone.` in a modal question (a `QMessageBox` like the create-library question, through an `ask_to_delete` seam in the same style). **Enter deletes, Esc keeps it**; Delete is the focused default button. `Del` on nothing (empty grid) does nothing; `Del` in the viewer does nothing.
- Deleting removes the file from the drive, then its rows from the drive's library (its tags and chapters; tag names nobody uses any more go too). The grid shows the folder again without it, the cursor on the tile that took its place (the previous one if it was last), and the status bar shows that tile's tags. Its stale thumbnail cache row is harmless (cache lookups check size and mtime).
- Same rule as tagging: deleting needs a library that can be saved (`tags_can_be_saved()`); otherwise `Can't delete here` flashes and nothing is asked. The app's own drive and the system disk never hold a library, so they're covered. If the file can't be deleted (drive gone, permissions), `Couldn't delete — is the drive still connected?` and the library is left alone.
- DESIGN.md (grid key table, a "Deleting" section) and the cheat sheet updated.

## Phase 30 — Del deletes a folder with everything in it

- `Del` on a folder tile asks `Delete folder "Holidays" and the 214 files in it? It can't be undone.` (`the 1 file`; an empty folder: `Delete empty folder "Holidays"?`). Count = every file under it, at any depth. Enter deletes the whole tree, Esc keeps it.
- The library loses the folder's row and every row under it (own tags, the tags its contents inherited, chapters). If deleting stops partway (a file can't be removed), what is left stays on the drive with its rows; only the rows of what is really gone are removed, and the error line of Phase 29 shows.
- The grid is shown again as in Phase 29.

## Phase 31 — Del in search results

- `Del` on a file or folder in search results asks and deletes as in Phases 29–30; the tile leaves the results (the results stay the same search, cursor as in Phase 29); coming back to the results from a slideshow still works. Esc back to the folder shows the folder without it.
- `Del` on a missing (`?`) result asks `Forget "IMG_0001.jpg"? Its tags are removed.` and removes only its library rows (the file is already gone).
