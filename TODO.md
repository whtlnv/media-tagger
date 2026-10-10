# TODO

Phase 7 notes for every cycle. Architecture: `viewer.py` must not grow. The grid lives in a new `src/mediatagger/grid.py` (a `QListView` in icon mode over a `QAbstractListModel` of the folder's entries, painted by a custom `QStyledItemDelegate`; each entry carries its path, kind — folder/image/video — and own-tag count, and leaves room for a thumbnail that Phase 8 will add) with its tests in `src/mediatagger/test_grid.py`. The one top-level window that switches between grid and viewer (a `QStackedWidget`) lives in a new `src/mediatagger/window.py` with tests in `src/mediatagger/test_window.py`; `main()` builds it instead of a bare `Viewer`. Launch memory (`state.json` under the config home) lives in a new `src/mediatagger/state.py` with `src/mediatagger/test_state.py`. Folder listing goes in `folder.py` (tests in `test_folder.py`), the one-query tag counts in `library.py` (tests in `test_library.py`). Shared machinery (status bar, open library, backups, status messages) is moved out of `viewer.py` into the window or a helper module as behaviour-preserving refactor steps with the suite green — never copied. Existing `Viewer(...)` constructor arguments and tests keep working (a `Viewer` built on its own still has its status bar). Tests run offscreen and silent (`player_options={"ao": "null"}`), close every window they open, and never touch real drives or `~`: use temp dirs and the seams (`is_mount_point=`, `app_location=`, `ask_to_create_library=`, `ask_to_restore_library=`, `backup_root=`, and a config-home seam). Every new top-level window calls `collect_garbage_on_the_gui_thread()`. Never stat or decode files while painting tiles. As soon as any code path writes `state.json`, `src/mediatagger/conftest.py` must point `XDG_CONFIG_HOME` at a per-test temp folder (autouse, exactly like `backups_never_reach_the_real_home_folder` does for `XDG_DATA_HOME`) so no test ever writes the real `~/.config`. No cycle opens on-screen windows or takes screenshots of the real display; the orchestrator does native verification itself.


## Phase 7 — Folder grid

- [x] Listing a folder gives its subfolders first, then its images and videos
- [x] Subfolders are listed in natural, case-blind order (`day2` before `day10`, `alpha` before `Beta`)
- [x] A folder listing leaves out non-media files
- [x] A folder listing leaves out folders whose name starts with `.` (`.mediatagger`, `.Trashes`, `.Spotlight-V100`, `.fseventsd`, `.hidden`) while listing a plain folder beside them
- [x] Asking the library for a folder's tag counts gives an item with two own tags a count of 2
- [x] Asking the library for a folder's tag counts gives an untagged item no count
- [x] A folder's tag counts leave out tagged items that live in other folders (including its subfolders)
- [x] Asking the library for the tag counts of a folder of 5,000 items runs one SQL query
- [x] The grid of a folder shows one tile per listed entry, subfolders first, in listing order
- [x] The grid opened on a folder at a given file has its cursor on that file
- [x] A folder tile draws the folder glyph, an image tile the image glyph and a video tile the video glyph
- [x] A video tile shows a ▶ badge
- [x] An image tile shows no ▶ badge
- [x] A tile whose filename is wider than the tile shows it truncated with an ellipsis
- [x] A tile whose filename fits shows it whole, with no ellipsis
- [x] A tile for an item with 3 own tags shows a `🏷3` badge
- [x] A tile for an untagged item shows no tag badge
- [x] A grid with no library (viewing only) shows no tag badges
- [x] In the grid, `→` moves the cursor to the next tile and `←` back
- [x] In the grid, `↓` moves the cursor one row down
- [x] In the grid, `+` makes the tiles bigger than their starting size of about 200 px
- [x] In the grid, `-` makes the tiles smaller than their starting size
- [x] In the grid, pressing `+` repeatedly stops growing the tiles at about 400 px
- [x] In the grid, pressing `-` repeatedly stops shrinking the tiles at about 100 px
- [ ] Repainting the grid after its files have been deleted from disk still paints their tiles, without reading the files
- [ ] Opening the grid of a folder of 5,000 files finishes within a time budget, like the 5,000-tag test
- [ ] The window opened on a folder path shows the slideshow of that folder at its first item
- [ ] In the window's viewer, `Esc` shows the grid of the current item's folder with the cursor on that item
- [ ] In the window's viewer, `Esc` after stepping to the second item puts the grid cursor on the second item
- [ ] In the window's viewer with the tag prompt open, `Esc` closes the prompt and stays in the viewer
- [ ] On the window's launch screen, `Esc` quits the app
- [ ] In the grid, `Enter` on a file starts that folder's slideshow at that file
- [ ] In the grid, `Enter` on a folder opens that folder's grid with the cursor on its first entry
- [ ] In the grid, `Backspace` opens the parent folder's grid with the cursor on the folder just left
- [ ] In the grid of a drive's mount point, `Backspace` stays on that grid
- [ ] In the grid, `Esc` quits the app
- [ ] In the grid, `f` toggles fullscreen
- [ ] Dropping a folder onto the grid starts that folder's slideshow
- [ ] Dropping a file onto the grid starts its folder's slideshow at that file
- [ ] Moving the grid cursor onto a tagged item shows its own tags, space-separated, in the status bar
- [ ] Moving the grid cursor onto an untagged item shows no tags in the status bar
- [ ] The library status (e.g. the read-only notice) stays visible in the status bar while the grid is shown
- [ ] A backup message started in the viewer stays visible in the status bar after `Esc` shows the grid
- [ ] Going from the viewer to the grid and back on the same drive makes no new backup
- [ ] Going from the viewer to the grid and back on the same drive does not ask again to create its library
- [ ] After tagging a file in the viewer, `Esc` shows its grid tile with the updated tag badge
- [ ] Showing a folder's grid records that folder and its drive's mount point in `state.json` under `$XDG_CONFIG_HOME/mediatagger/`
- [ ] Showing a folder's slideshow records that folder in `state.json`
- [ ] With `XDG_CONFIG_HOME` unset, the state is recorded under `<home>/.config/mediatagger/` of the injected home
- [ ] The state file is not written when it would land on the app's own drive
- [ ] The state file is not written when it would land on the drive being viewed
- [ ] Launching the window with no path, when the remembered folder exists, opens that folder's grid
- [ ] Launching the window with no path into a remembered folder's grid opens that drive's library
- [ ] Launching the window with no path, when the remembered folder no longer exists, shows the launch screen
- [ ] Launching the window with no path and no state file shows the launch screen
- [ ] Launching the window with no path and an unreadable state file shows the launch screen
- [ ] Running the shipped `mediatagger <folder>` command shows one window whose `Esc` switches from the slideshow to that folder's grid
  - predicted-contradiction: `src/mediatagger/test_main.py::test_pressing_esc_in_the_mediatagger_command_makes_it_exit_cleanly` — asserts: pressing `Esc` in the slideshow of `mediatagger <folder>` makes the command exit cleanly — retired-by: "`Esc` switches from the slideshow to that folder's grid"
- [ ] Running the shipped `mediatagger` command with no path, after a folder was viewed, opens that folder's grid
