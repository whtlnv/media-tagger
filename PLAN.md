# MediaTagger — Plan

Delivery phases, in order. Decisions, key maps and rules live in `DESIGN.md`; every phase follows it.
Each phase must end with its behavior reachable from the shipped `mediatagger` command, not only from tests.


Phases 1–19 are delivered. Their specs are in git history (`PLAN.md` at `fcd5d3b` for 1–11, at `ca048de` for 12, at `76e644f` for 13, at `5ba4a0a` for 14, at `9a27389` for 15, at `213f913` for 16, at `f1a53c2` for 17, at `4cc0f4e` for 18, at `a2d1a4e` for 19) and their items in `DONE.md`.

## Phase 20 — The search label leaves the viewer

From the user's Pi run of 2026-10-16 (`results/findings.txt`): "when searching and then playing one of the results, the search bar remains visible. When viewing one of the results, the search bar is not useful."

- What stays on screen is the `Search: <query>` label above the results grid (`Window.breadcrumb`). It belongs to the results grid only: opening a file from search results (slideshow, image or video) hides it; `Esc` back to the results shows it again with the same query; leaving the results (`Esc` to the folder, or opening a folder result) hides it as today.
- Nothing else about search changes. Check that no other overlay meant for a grid (filter button, grid status text) stays over the viewer either; fix any you find the same way.

## Phase 21 — Viewer: rotate images, zoom to 500 %, frame step

From the same Pi notes.

- **`r` turns images too**, 90° clockwise each press, the picture still fitted whole to the screen, exactly like videos. Every item opens unrotated; nothing is saved; thumbnails are unchanged. `r` keeps the zoom, and zoom/pan stay correct on a rotated picture (anchored at the pointer, no black inside the window, centred at 100 %). DESIGN.md's `r` row loses "(video)".
- **Zoom goes to 500 %** (was 300 %), for images and videos, same 10-point steps. The sharper re-decode of a photo when zooming never decodes past the photo's own pixel size (memory on the Pi).
- **Frame step:** with a video paused, `u` shows the next frame and `e` the previous one (the user asked for `p`/`y`, but `p` is play/pause). While playing they do nothing. The progress bar follows. Added to DESIGN.md's viewer table and the cheat sheet; typed into the tag prompt they type letters.
