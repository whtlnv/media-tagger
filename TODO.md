# TODO

Phase 15 follow-up notes for every cycle (the user's decision of 2026-10-15 after the native check: the sheet drawn as a background was hidden by tiles and media, so it becomes a dim overlay on top) (Phases 1–14 are delivered — see DONE.md; Phases 16–18 are later deliveries — decompose only "Phase 15 — Key cheat sheet"). Spec: PLAN.md "Phase 15". **Constraints** — tests are co-located with source (`src/mediatagger/test_*.py`), one test at a time, offscreen and silent (`player_options={"ao": "null"}`), never touch real drives or `~`; create mpv players only via `video.new_engine()`; keep `gui_thread_gc` in force; teardown tests flush `QEvent.Type.DeferredDelete`. Never pass `None` (e.g. `QApplication.focusWidget()` offscreen) to `QTest.keyClick` — check the widget exists first. `viewer.py` is at 266 of its 270-line budget and must not grow past 270 — the viewer only paints the sheet; everything else lives in `cheat_sheet.py`. Never write to `/Volumes/MEDIATAGGER`, never touch `spikes/`. Another project's test suite sometimes loads this Mac: if a timing test fails, rerun before concluding.

**Design for the follow-up (decided by the orchestrator; follow it):**
- `cheat_sheet.py` keeps `GRID_KEYS`, `VIEWER_KEYS`, `LAUNCH_KEYS` (still pinned against DESIGN.md's tables) and `CheatSheet` becomes a `QWidget` overlay, a child of the Window covering the whole window, transparent to the mouse (wheel, drops and clicks reach what is under it), never taking focus, kept above the stack (so above a playing video's `MpvSurface`, which lies inside the stack). It paints a centred panel — dark translucent rounded backing, light text, one `key  meaning` line per key — through a module function `draw_sheet(painter, rect, keys)` that tests can use to draw the expected picture. The keys come from a callable the Window supplies: the grid's keys while a grid is shown, the viewer's keys while an item is shown, the launch keys while the viewer shows nothing.
- `h` and `Esc` are caught by `CheatSheet.watch(widget)` (event filter on the viewer and every grid, as now): `h` toggles; `Esc` while shown hides it and is consumed (doesn't quit or go back) — except while a line edit (tag prompt) has focus, where `Esc` keeps closing the prompt. Every other key passes through untouched.
- Shown/hidden stays remembered in `state.json` exactly as now. The background painting in the grid and viewer, and the grid's full repaint on scroll, go.

- [x] In the window's grid, pressing `h` draws a panel of the grid's keys over the middle of the window, on top of the tiles
- [x] The tiles stay visible through the panel: a red tile under it still shows red, darkened
- [x] In the window's grid, pressing `h` a second time removes the panel, leaving the window as it was before
- [x] In the window's viewer showing an image, pressing `h` draws a panel of the viewer's keys over the middle of the window, on top of the picture
- [x] On the window's empty launch screen, pressing `h` draws a panel of the launch screen's keys
- [x] With the panel shown in the grid, opening an image shows the viewer's keys, and `Esc` back to the grid shows the grid's keys again
- [ ] With a video playing in the window's viewer, the shown panel is stacked above the video
- [ ] Pressing `Esc` while the panel is shown in the grid hides it and leaves the window open on the grid
- [ ] Pressing `Esc` while the panel is shown in the viewer hides it and leaves the viewer showing the same item
- [ ] With the panel shown, the arrow keys still move the grid's cursor
- [ ] With the panel shown, `Esc` in the viewer's tag prompt closes the prompt and leaves the panel shown
- [ ] The grid and viewer no longer draw the sheet behind tiles or pictures: with the panel shown, the window's corners away from the panel look as they do with it hidden
