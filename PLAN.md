# MediaTagger — Plan

Delivery phases, in order. Decisions, key maps and rules live in `DESIGN.md`; every phase follows it.
Each phase must end with its behavior reachable from the shipped `mediatagger` command, not only from tests.


Phases 1–20 are delivered. Their specs are in git history (`PLAN.md` at `fcd5d3b` for 1–11, at `ca048de` for 12, at `76e644f` for 13, at `5ba4a0a` for 14, at `9a27389` for 15, at `213f913` for 16, at `f1a53c2` for 17, at `4cc0f4e` for 18, at `a2d1a4e` for 19, at `65d51a2` for 20) and their items in `DONE.md`.

## Phase 21 — Zoom to 500 %

From the same Pi notes.

- The mouse-wheel zoom goes to 500 % (was 300 %), for images and videos, same 10-point steps. The sharper re-decode of a photo when zooming never decodes past the photo's own pixel size (memory on the Pi). DESIGN.md's wheel row updated.

## Phase 22 — Frame step on a paused video

From the same Pi notes ("next and previous frames using 'p' and 'y' if available, if not maybe 'e' and 'u'"; `p` is play/pause).

- With a video paused, `u` shows the next frame and `e` the previous one (Dvorak: `e` sits left of `u`). While playing they do nothing. The progress bar follows. Added to DESIGN.md's viewer table and the cheat sheet; typed into the tag prompt they type letters.

## Phase 23 — `r` turns images too

From the same Pi notes.

- `r` turns an image 90° clockwise each press, the picture still fitted whole to the screen, exactly like videos. Every item opens unrotated; nothing is saved; thumbnails are unchanged. `r` keeps the zoom, and zoom/pan stay correct on a rotated picture (anchored at the pointer, no black inside the window, centred at 100 %). DESIGN.md's `r` row loses "(video)".
