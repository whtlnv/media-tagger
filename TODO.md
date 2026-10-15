# TODO

Phase 16 notes for every cycle (Phases 1–15 are delivered — see DONE.md; Phases 17–18 are later deliveries — decompose only "Phase 16 — Required tags"). Spec: PLAN.md "Phase 16" (decided by the user; authoritative). **Constraints** — tests are co-located with source (`src/mediatagger/test_*.py`), one test at a time, offscreen and silent (`player_options={"ao": "null"}`), never touch real drives or `~` (drives are faked with `is_mount_point=` seams as in the existing window tests); create mpv players only via `video.new_engine()`; keep `gui_thread_gc` in force. Never pass `None` (e.g. `QApplication.focusWidget()` offscreen) to `QTest.keyClick`. `viewer.py` is at 266 of its 270-line budget and must not grow — this phase needs nothing in it. Never write to `/Volumes/MEDIATAGGER`, never touch `spikes/`. Another project's test suite sometimes loads this Mac: if a timing test fails, rerun before concluding.

**Design (decided by the orchestrator; follow it):**
- New module `drive_config.py`: `CONFIG_FILE = "mediatagger_config.json"`, `CONFIG_CANT_BE_READ_TEXT = "mediatagger_config.json can't be read — no tiles marked"` and `required_roots(drive)` returning `(roots, problem)` — `roots` a tuple of lowercased root strings (empty with no file, no `requiredRoots`, or a problem), `problem` `None` or the text above when the file exists but can't be read (OSError, not UTF-8) or isn't valid (not JSON, not an object, `requiredRoots` not a list of strings). It only opens the file for reading; it never writes. A pure function `missing_roots(tags, roots)` gives how many roots none of `tags` starts with.
- `DriveSession` reads the config whenever it opens a drive different from the current one (launch, `o`, a drop — the same place it opens the library), keeps `session.required_roots`, and shows the problem text in a dedicated status-bar label (`StatusBar.show_config_problem(text)`, hidden when empty), cleared when another drive opens.
- Tiles are marked only when a library is open (with none, nothing is tagged and no tile is marked) and only file tiles (folders and missing results are never marked). `_Tile` gains `missing: int = 0`; `Grid(..., required_roots=())` computes it at listing time from bulk reads: a folder grid reads its folder's own effective tags once (`library.effective_tags(folder)`, own + inherited) plus its direct items' own tags in one query (a new `Library` method alongside `tag_counts`); a results grid uses `library.tagged_items()` (one query) and each result's ancestors from that map. Never one query per tile. With no roots, nothing extra is read.
- The badge text is `✗<n>` (`MISSING_BADGE = "✗"`), drawn by `_draw_backed_badge` in the top-right corner immediately left of the tag-count badge's backing (or in the corner itself when there is no tag badge).
- After the tag prompt saves (grid) the current grid recomputes every tile's tag count and mark from fresh bulk reads (covers a folder whose tags reach other shown tiles); returning with `Esc` from a results slideshow to the same results grid recomputes them too (a fresh folder grid already reads fresh data).
- `Window._grid_of` and `run_search` pass `self.session.required_roots` to `Grid`.

- [x] `required_roots` of a drive whose root holds `mediatagger_config.json` with `{"requiredRoots": ["type:", "size:"]}` gives those two roots and no problem
- [x] `required_roots` of a drive with no config file, or one with no `requiredRoots`, gives no roots and no problem, and leaves the drive's file list unchanged
- [x] `required_roots` of a drive whose config isn't valid JSON gives no roots and the "can't be read" problem text
- [x] `required_roots` of a drive whose config is JSON but whose `requiredRoots` isn't a list of strings (or which isn't an object) gives no roots and the problem text
- [x] `required_roots` of a drive whose config can't be read (e.g. a folder named `mediatagger_config.json`, or bytes that aren't UTF-8) gives no roots and the problem text
- [x] `missing_roots` counts the roots that none of the given tags starts with (`["type:photo"]` against `type:`, `size:` → 1)
- [ ] A grid given required roots `type:` and `size:` paints `✗2` on the tile of a file in its folder with no tags at all
- [ ] A file tile whose own tags start with every required root paints no `✗` badge
- [ ] A file whose missing root is covered by a tag inherited from its folder or an ancestor folder is not counted as missing it (`✗1` when only `type:` is inherited and `size:` is missing)
- [ ] A folder tile, even an untagged one, never paints a `✗` badge
- [ ] A grid with no required roots, or with no library, paints no `✗` badge on any tile
- [ ] On a tile with both badges, the `✗` badge sits in the top row to the left of the tag-count badge, the two not overlapping, the tag-count badge still in the top-right corner
- [ ] The `✗` badge reads white on a dark backing over both a white and a black thumbnail, like the tag-count badge
- [ ] A results grid given required roots marks each result file by its effective tags (own tags and those of its ancestor folders in the library), and never marks a result folder or a missing result
- [ ] After a first grid has been shown, opening and showing the grid of a folder of 5,000 files in a library where half are tagged, with two required roots, takes under 150 ms
- [ ] In the window, opening a folder on a fake drive whose root holds a config naming `type:` and `size:` shows the grid with its untagged file's tile marked `✗2`
- [ ] In the window, opening a folder on a fake drive with no config shows no `✗` badge on any tile
- [ ] In the window, opening a drive whose config isn't valid JSON shows the "can't be read" text in the status bar and no `✗` badge on any tile, and the app keeps working (the grid opens)
- [ ] In the window, after opening a drive with an invalid config, switching to another drive (e.g. by a drop) with a valid config clears the status-bar text and marks that drive's tiles by its own config
- [ ] In the window's grid, tagging the cursor's file `type:photo` with the tag prompt changes its mark from `✗2` to `✗1` at once, and adding `size:big` then removes the mark
- [ ] In the window's results grid, tagging a result file with a missing root updates its mark at once
- [ ] In the window, tagging a result file in the viewer opened from a results grid and pressing `Esc` back to the results shows its updated mark (and tag count)
- [ ] Running the app opens the drive's config without writing to the drive: after opening a drive with a config and browsing it, the drive root's files and the config's bytes and mtime are unchanged
