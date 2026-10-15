# TODO

Phase 14 notes for every cycle (Phases 1–13 are delivered — see DONE.md; Phases 15–18 are later deliveries — decompose only "Phase 14 — Zoom"). Spec: PLAN.md "Phase 14". 100 % is the fitted size the viewer shows today; one wheel notch is one step; never below 100 %, never above 300 %. "The point under the mouse stays under the mouse" means the media pixel under the cursor before a notch is under the cursor after it (within a pixel or two). Images are drawn by `Viewer.paintEvent` from `image_fit`; videos by `MpvSurface` (a child widget covering the viewer, so wheel events over a video land on it). Rotation exists for videos only (`r`, Phase 13). **Constraints** — tests are co-located with source (`src/mediatagger/test_*.py`), one test at a time, offscreen and silent (`player_options={"ao": "null"}`), never touch real drives or `~`; create mpv players only via `video.new_engine()`; keep `gui_thread_gc` in force; teardown tests flush `QEvent.Type.DeferredDelete`. `viewer.py` is at 265 of its 270-line budget and must not grow past 270 — move code out rather than grow it. Never write to `/Volumes/MEDIATAGGER`, never touch `spikes/`. Another project's test suite sometimes loads this Mac: if a timing test fails, rerun before concluding.

**Design for this phase (decided by the orchestrator; follow it):**
- Put the zoom in a new module `src/mediatagger/zoom.py` (tests in `test_zoom.py` where pure maths needs pinning) — the viewer only forwards the wheel and draws/applies the result. Do not grow `viewer.py` past 270 lines; move code out of it if needed.
- **Model** (the same as mpv's): a zoom is a level `z` in [1, 3] and a pan `(px, py)` in fractions of the zoomed picture's size. Given the fitted rect `F` (today's `image_fit.fitted_rect`) and the window `W`, the shown rect `R` has size `F.size * z` and centre `W.centre + (px * R.w, py * R.h)`. At 100 % the pan is (0, 0), so `R == F`.
- **Step:** one notch (`angleDelta().y() == 120`) changes the level by 0.1 (10 percentage points), finer deltas (trackpads) pro rata; up (positive) zooms in. Clamped to [1, 3].
- **Point under the mouse:** the new rect is the old one scaled about the cursor `c` by `z'/z` (`R' = c + (R - c) * z'/z`).
- **No empty space (cheap clamp):** on each axis, after scaling, the picture's left/top edge is clamped to `[min(0, W - R'), max(0, W - R')]` — a picture bigger than the window always covers it, one smaller lies inside it. So zooming in from a picture that already covers the window on an axis keeps the point exactly; the point drifts only when an edge would otherwise come away from the window side (zooming out near an edge, or a letterboxed axis growing past a window edge). **Tests of "the point stays" must therefore use media whose aspect matches the window (or check only an axis where no clamp applies).**
- **Images:** `paintEvent` draws the decoded image into `R` instead of `F`. Wheel events go to `Viewer.wheelEvent` (labels and the `MpvSurface` child ignore wheel events, so Qt passes them up to the viewer). Today the image is decoded no larger than the window; once zoomed past 100 % decode it once more, no larger than 3x the window (the cache key gains "zoomed or not"), so 300 % shows real detail without a decode per notch.
- **Videos:** apply the same `z` and pan to mpv: `video-zoom = log2(z)`, `video-pan-x = px`, `video-pan-y = py` (mpv's pan unit is a fraction of the scaled video's size; align stays 0 = centred). `F` for a video is the fit of its display size (`dwidth`/`dheight`, swapped when `video-rotate` is 90/270) in the surface. Pin the pan maths with `test_video_fit.py`'s headless CGL pixel readback (macOS-only skip already there): pick a surface with black bars on the axis you check, so the drawn box reveals the pan (e.g. the 64x48 clip on a 300x150 surface is fitted 200x150 at x 50..249).
- **Reset:** a new item (next/previous, open, drop) starts at 100 %. `VideoPlayer.show` already resets `video_rotate` before loading — reset `video_zoom`/`video_pan_x`/`video_pan_y` there too. `r` keeps the zoom level and recentres the picture (pan 0, re-clamped against the turned fit).
- **State so far:** `zoom.Zoom` (level only, multiplicative 1.25 placeholder step, floor 1) is used by `Viewer.paintEvent`/`wheelEvent`. Grow the maths in `zoom.py`, not in `viewer.py` (now 271 lines — bring it back to ≤270 when you next touch it). The 1.25 step is a placeholder: the 300 % cap item should switch it to the planned +0.1 per notch.
- **Measuring offscreen:** the viewer's status bar and overlay labels are drawn over the picture (the bottom ~30 rows at least), so a test counting picture pixels down a whole column never reaches the window's full height — measure across a row through the centre, or between bounds clear of the overlays, or look at specific marker pixels.
- No zoom indicator (the spec doesn't ask for one). Wheel with no item shown does nothing.

- [x] Scrolling the mouse wheel up one notch over a fitted image shows it larger than fitted
- [x] Scrolling the mouse wheel down one notch over a fitted image leaves it fitted
- [x] Scrolling the mouse wheel down one notch over a zoomed-in image shows it smaller than before, still no smaller than fitted
- [x] Scrolling the mouse wheel up many notches over an image stops at three times its fitted size
- [ ] A photo larger than the window, zoomed in to 300 %, shows its own fine detail rather than an enlarged copy of its fitted size
- [ ] Zooming in on an image with the mouse near its top-left corner keeps the image point under the mouse under the mouse
- [ ] Zooming in on an image with the mouse near its bottom-right corner keeps the image point under the mouse under the mouse
- [ ] Zooming out of a zoomed-in image, without reaching fitted, keeps the image point under the mouse under the mouse
- [ ] Moving to the next item after zooming in on an image, then back, shows that image fitted again
- [ ] Scrolling the mouse wheel up one notch over a playing video shows it larger than fitted
- [ ] Scrolling the mouse wheel down one notch over a fitted playing video leaves it fitted
- [ ] Scrolling the mouse wheel down one notch over a zoomed-in video shows it smaller than before, still no smaller than fitted
- [ ] Scrolling the mouse wheel up many notches over a video stops at three times its fitted size
- [ ] Zooming in on a playing video with the mouse off its centre keeps the video point under the mouse under the mouse
- [ ] Zooming in on a video turned 90° with `r`, with the mouse off its centre, keeps the video point under the mouse under the mouse
- [ ] Pressing `r` on a zoomed-in video turns it and keeps it zoomed in
- [ ] Moving to the next video after zooming in on a video shows the next video fitted
- [ ] In the window the `mediatagger` command builds, scrolling the mouse wheel up over a playing video in the viewer shows it larger than fitted
