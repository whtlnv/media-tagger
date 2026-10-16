# TODO

Phase 17 notes for every cycle (Phases 1–16 are delivered — see DONE.md; Phase 18 is a later delivery — decompose only "Phase 17 — Grid filters"). Spec: PLAN.md "Phase 17" (decided by the user; authoritative). **Constraints** — tests are co-located with source (`src/mediatagger/test_*.py`), one test at a time, offscreen and silent (`player_options={"ao": "null"}`), never touch real drives or `~` (drives are faked with `is_mount_point=` seams as in the existing window tests); create mpv players only via `video.new_engine()`; keep `gui_thread_gc` in force. Never pass `None` (e.g. `QApplication.focusWidget()` offscreen) to `QTest.keyClick` or the mouse helpers. `viewer.py` is at 266 of its 270-line budget and must not grow — this phase needs nothing in it; keep `grid.py` and `window.py` from growing much (the button, its menu and the filter rules go in a new module). Never write to `/Volumes/MEDIATAGGER`, never touch `spikes/`. Another project's test suite sometimes loads this Mac: if a timing test fails (the 3 s quit tests in `test_main`, `drive/test_run.py`'s startup test), rerun before concluding. Never open a menu with the blocking `QMenu.exec` in a test — the button pops its menu up without blocking.

**Design (decided by the orchestrator; follow it):**
- New module `grid_filter.py`: the menu texts `WITH_TAGS = "With tags"`, `NO_TAGS = "No tags"`, `MISSING_TAGS = "Missing tags"`; `GridFilter(QObject)` holding `active` (`None` or one of the texts), `choose(text)` (choosing the active one again sets `None`) and a `changed` signal — one per `Window`, shared by every grid it builds (folder grids and results), never saved (lasts while the app runs); and `FilterButton`, the round floating button.
- **What matches** (on file tiles only — folder tiles and missing result tiles always stay): With tags = the file has own tags (the tag-count badge shows, `tag_count > 0`); No tags = it has none (`tag_count == 0`), whatever it inherits; Missing tags = it carries a `✗` mark (`missing_roots > 0`, by effective tags, Phase 16). Own tags, not effective, so a filter agrees with the badge the user sees on each tile.
- `Grid(..., grid_filter=None)`: with none there is no button and nothing is filtered (existing tests stay as they are). `Window` passes its one `GridFilter` to `_grid_of` and to `run_search`'s results `Grid`. Non-matching file rows are hidden in place (`setRowHidden`), so the model, rows and thumbnail bookkeeping are unchanged; thumbnails are not requested for hidden rows.
- The filter is applied when the grid opens, again whenever it changes (the shown grid updates at once), and again after `show_new_tags` — so tagging a file so it no longer matches hides it **at once** (as marks update at once).
- **Cursor:** whenever the cursor would sit on a hidden tile (a filter chosen, a tag saved, a grid opened `at=` a hidden file, the first tile of a folder that opens), it goes to the next shown tile after it, else the nearest shown one before it, else nowhere (and the status bar's tags clear).
- **Button** (`FilterButton`, a child of the grid, raised over its viewport): round, ~40 px, never takes keyboard focus (mouse only; no key binding; `h`'s cheat sheet keys are unchanged), at the grid's bottom-right corner just above the bottom margin the grid keeps clear for the status bar and left of the vertical scroll bar, about 12 px in; re-placed on every grid resize (fullscreen included). Off: a translucent dark backing (tiles read through it). On: drawn checked in the highlight colour, opaque, and its tooltip names the active filter. A click pops up (without blocking) a `QMenu` of checkable actions, the active one checked: With tags, No tags, and Missing tags only when the grid has a library and required roots — or when Missing tags is the active filter, so it can always be turned off. Triggering an action calls `GridFilter.choose`.
- **Slideshow:** `Enter` on a file of a filtered grid (folder or results) starts the slideshow over the files shown (in grid order), like a results slideshow; with no filter it is as today. `Esc` back puts the cursor on the current file, or the next shown one if it no longer matches.
- The cheat sheet (mouse-transparent) never blocks a click on the button; DESIGN.md's key tables stay as they are (the button isn't a key).


- [x] In a folder grid sharing the window's filter, with no filter chosen, every file tile shows
- [x] With "With tags" chosen, a folder grid hides a file that has no own tags
- [x] With "With tags" chosen, a folder grid keeps showing a file that has own tags
- [x] With "With tags" chosen, a file whose only tags are inherited from its folder is hidden
- [x] With "No tags" chosen, a folder grid hides a file that has own tags
- [x] With "No tags" chosen, a folder grid keeps showing a file with no own tags, even one that inherits tags
- [x] With "Missing tags" chosen, a folder grid hides a file that carries no `✗` mark
- [x] With "Missing tags" chosen, a folder grid keeps showing a file that carries a `✗` mark
- [x] Under any filter, folder tiles stay shown
- [x] Choosing a second filter replaces the first: only the second one's matches show
- [x] Choosing the active filter again turns filtering off and every tile shows again
- [x] Choosing a filter while a grid is shown hides its non-matching files at once
- [x] A filter chosen in one folder's grid applies to the next folder opened in the same window
- [x] A new window starts with no filter, whatever was chosen in an earlier window
- [x] Under a filter, a search results grid hides result files that don't match
- [x] Under any filter, a search results grid keeps showing missing result tiles
- [x] Under "With tags", removing a file's last own tag from the grid's tag prompt hides it at once
- [x] Under "No tags", adding a tag to a shown file from the grid's tag prompt hides it at once
- [x] Under "No tags", adding a tag to a file's folder leaves the file shown
- [x] Choosing a filter that hides the cursor's tile moves the cursor to the next shown tile after it
- [x] Choosing a filter that hides the cursor's tile, with no shown tile after it, moves the cursor to the nearest shown tile before it
- [x] Choosing a filter that leaves the cursor's tile shown keeps the cursor where it is
- [x] Choosing a filter that hides every file of a folder with no subfolders leaves no cursor and clears the status bar's tags
- [x] Opening a folder whose first tile is hidden by the filter puts the cursor on the first shown tile
- [x] Going up to a folder at a child that the filter hides puts the cursor on the next shown tile after it
- [x] Saving a tag that hides the cursor's file moves the cursor to the next shown tile
- [x] A grid under a filter requests no thumbnail for a hidden file
- [x] A grid under a filter requests thumbnails for its shown files in view
- [x] A grid sharing the window's filter shows a round filter button at its bottom-right corner, above the status bar's clear margin and left of the vertical scroll bar
- [x] A grid given no shared filter shows no filter button
- [x] After the grid is resized (fullscreen included), the filter button sits at its new bottom-right corner
- [x] Clicking the filter button leaves keyboard focus on the grid, so arrow keys still move the cursor
- [x] With no filter on, the filter button is drawn with a translucent dark backing
- [x] With a filter on, the filter button is drawn checked, opaque, in the highlight colour
- [x] With a filter on, the filter button's tooltip names the active filter
- [x] Clicking the filter button pops up a menu offering "With tags" and "No tags", the active filter checked
- [x] The filter menu offers "Missing tags" when the grid's library has required roots
- [x] The filter menu doesn't offer "Missing tags" when the drive has no required roots
- [x] The filter menu offers "Missing tags" when it is the active filter, even without required roots
- [x] Triggering an action in the filter menu chooses that filter
- [x] With the cheat sheet shown over the grid, a click on the filter button still pops up its menu
- [ ] `Enter` on a file of a filtered folder grid starts a slideshow over only the shown files, in grid order
- [ ] After the filter is turned off again, `Enter` on a file starts a slideshow over every file of the folder
- [ ] `Enter` on a file of a filtered results grid starts a slideshow over only the shown result files
- [ ] `Esc` back from a filtered slideshow puts the cursor on the file that was showing
- [ ] `Esc` back from a filtered slideshow on a file tagged so it no longer matches puts the cursor on the next shown tile
- [ ] In the shipped `mediatagger` app, clicking the grid's filter button and choosing "No tags" hides the folder's tagged files
