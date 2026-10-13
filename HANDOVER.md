# Handover — MediaTagger

State of the project and how it has been run, for the next session. Read `DESIGN.md` (decisions) and `PLAN.md` (phases) first; this file is the "how we work" and "where we are" layer on top.

## Where we are

| Phase | Status |
|---|---|
| 1 Viewer & slideshow | done, validated |
| 2 Drag & drop, launch screen | done, validated |
| 3 Library on the drive | done, validated |
| 4 Tag the current file | done, validated |
| 5 Autocomplete | done, validated |
| 6 Database backups | done, validated |
| 7 Folder grid | done, validated (415 tests) |
| 8 Thumbnails | done, validated; first Pi run 2026-10-11 found a per-frame fd leak in video playback (Pi only) and an Esc-to-grid error — see Phase 9a |
| 9 Tag folders & inherited tags | done, validated (557 tests) |
| 9a Pi fixes & video controls | done, validated on the Mac (`1402d2e`, 605 tests); Pi run pending |
| 9b Video playback never leaks | done, validated on the Mac (`946d17b`, 611 tests); Pi run pending — see "Video crash on the Pi" |
| 10 Search | done, validated on the Mac (`c54a2a5`, 695 tests); Pi timing unmeasured — see "Phase 10 — done" |
| 11 Run from the drive on the Pi | not started (spike tooling exists in `spikes/drive/`) |

Code: `src/mediatagger/` — `window.py` (top-level, switches grid ⇄ viewer), `grid.py`, `viewer.py`, `tag_prompt.py` (the `t` prompt, shared by grid and viewer), `status_bar.py`, `drive_session.py` (library open/create/restore/backup), `library.py` (SQLite, schema v2), `backup.py`, `state.py` (last folder, geometry, recent searches; `$XDG_CONFIG_HOME`), `search.py` (query matching), `search_bar.py` (the `/` box and its `↑`/`↓` history), `folder.py`, `slideshow.py`, `thumbnails.py` (image/video/folder thumbnails, `ffmpeg`/`ffprobe`), `thumbnail_cache.py`, `thumbnail_scheduler.py` (3 workers + prefetch), `folder_thumbnails.py` (a folder's thumbnails for its grid), `video.py` + `mpv_surface.py` (libmpv render API), `video_controls.py` (Phase 9a: video progress bar — in progress), `gui_thread_gc.py`. Tests are co-located (`test_*.py`). Open structural debt is in `BACKLOG.md`.

## How the work has been run

- One Opus subagent per PLAN phase, strictly in order, each invoking the `tdd-deliver` skill (falling back to `tdd-supervise`). The orchestrator (main session) writes a detailed brief, monitors progress, then **validates** before starting the next phase:
  - full suite twice (`.tdd-test-cmd`; ~340+ tests, ~1 min),
  - read the diff of production code for scope creep and structure,
  - native check on the real screen (see below),
  - no new crash reports from this project,
  - send the agent back with a numbered fix list if anything is off.
- Progress is relayed to the user in chat from a `Monitor` that polls `git log`, `TODO.md` checkbox counts, `~/Library/Logs/DiagnosticReports/Python-*.ips` and `/Volumes/MEDIATAGGER`. Monitors expire every 30 min; re-arm.
- The user asked for progress to be printed in the conversation and for questions only when a decision is genuinely theirs.

## Phase 10 — done

Spec: PLAN.md "Phase 10"; the agent's decisions (query syntax, whole-drive scope, folders-first natural order, `/` needs a library, Backspace inert in results, ❓ missing tiles, results slideshow skips folders/missing, 50 searches newest last) are listed in DESIGN.md "Search" and may be overruled by the user. Delivered 80 items + 14 closing-check fixes; native check (2026-10-13) found 3 more, fixed with tests (`1ad5a3c` breadcrumb rendered the query as rich text, `1add39b` empty results kept the previous item's tags in the status bar, `910865e`/`c54a2a5` bar and breadcrumb in a tiny default font — now the status bar's style). Checked natively: AND/NOT/OR/prefix results, collapse into the top-most folder, missing tile, slideshow over results and Esc back to them, `↑` recall, result folder opens normally, fullscreen, `searches` saved in `state.json`.

- **Not checked natively:** search speed on the Pi (33 ms for 5,000 items on the Mac; budget test is 50 ms) and the results grid's per-path existence checks on a USB stick (~80 ms/5,000 on the Mac).
- **Known:** keypad Enter is not handled anywhere in the app (only `Key_Return`); back from a results slideshow, unloaded result thumbnails stay as glyphs (BACKLOG).
- The `test_grid` 5,000-image timing test failed once while another test run was loading the machine; passes on an idle machine (BACKLOG already notes its GC sensitivity).

## Phase 9a — done

Spec: PLAN.md "Phase 9a" (all behaviours decided by the user, 2026-10-11). Delivered 39 items; native check (2026-10-12) found 3 bugs offscreen tests can't see — progress bar stacked under the mpv surface, `ShutdownError` from the bar's tick when closing mid-video, `f` in the viewer toggling the child widget instead of the window (pre-existing, hidden by the old fullscreen start) — all fixed with regression tests (`afe05a3`, `f6d122a`, `1402d2e`). Checked natively: bar readable over black and white video, fades after 3 s and returns on any key, sits above the tag prompt; `h:mm:ss` for an hour-long clip; `0`–`9` and `↑`/`↓` seek; window opens at 80 % centred on 2560x1080; closing while fullscreen remembers the normal geometry and relaunch restores it; macOS pulls an off-screen remembered position back on screen.

- **Not checked natively:** window start on the rotated 1080x1920 display (the app centres on the screen it is created on; the user may drag it there and relaunch).
- **Known:** a video whose duration mpv reports as None/0 would raise in `ProgressBar._show_elapsed` (no sample triggers it; a pipe-written mkv and a one-frame clip both work).

## Video crash on the Pi — root cause found, fix built and checked on the Mac (Phase 9b); Pi run pending

- Symptom (first Pi run, build `ff64cc3`): video plays ~30–40 s, then `Too many open files` → Wayland connection dies → app exits. `diag-video.sh`: +1 `anon_inode:sync_file` fd per frame, regardless of mpv decode options or Wayland/XWayland. `diag-video3.sh`: the real app leaks (~15/s, fullscreen and windowed); the diag replicas didn't — but they never actually rendered per frame (their `QTimer.singleShot` from mpv's thread never fired), so diag2/diag3 replica rows prove nothing about mpv-in-Qt. Qt GL redraw alone and mpv in its own window (`vo=gpu`, `wid`) genuinely don't leak.
- **Root cause (mpv 0.40 bug, render API + OpenGL):** `video/out/opengl/libmpv_gl.c` `done_frame` → `ra_gl_ctx_submit_frame` (`context.c:235`) creates a `glFenceSync` after every rendered frame and appends it to `vsync_fences`; those are only deleted in `ra_gl_ctx_swap_buffers`, which the libmpv render path never calls. So one GL fence leaks per frame on every platform; on the Pi's Mesa v3d each fence holds a `sync_file` fd → fd exhaustion. Regressed in 0.40.0; fixed on mpv master by f74adc4 (2026-01-22, mpv#17217) but in no release yet (latest v0.41.0) nor any Debian package.
- **Proven on the Mac (2026-10-12):** a QOpenGLWidget + render-API test redrawn per frame (like `MpvSurface`) had 443 live fences after 15 s (1 per frame, never deleted); with the workaround, 0 live fences and playback unaffected (30 fps). Script: `spikes/fence_check_mac.py` (wraps `glFenceSync`/`glDeleteSync` through the proc-address callback and counts).
- **Fix (Phase 9b, built):** `mpv_surface.fence_free_lookup` wraps the context's GL lookup so `glFenceSync` resolves to a ctypes stub returning `NULL` (mpv skips storing a null fence: `if (fence)`); `MpvSurface.initializeGL` hands it to mpv. The viewer's player options include `vd-lavc-dr=no`, because mpv's only other fence use (`ra_gl.c` host-mapped PBOs, used by direct rendering) would otherwise treat buffers as immediately reusable. Do **not** simply hide `glFenceSync` — `GL_ARB_sync` is core in GLES 3 (the Pi) and mpv refuses to init if a core function is missing (`common.c` `must_exist`). Mac native check done (2026-10-12): in the real app, live GL fences stay 0 on H.264 1080p, HEVC 1080p and 4K (unfixed: ~30/s), mpv calls the stub once per frame, playback real-time, `vd-lavc-dr` off. Still to do: a Pi run counting `sync_file` fds of the app (`diag-video3.sh`'s app rows) → flat, and play a video for minutes — `mediatagger/check-video-leak.sh` on the stick does both and copies its log to `results/` after the app exits.
- Upstream: already reported (mpv#17217) and fixed (f74adc4), unreleased. Full write-up, C repro and where-to-report table: `spikes/mpv-fence-leak/REPORT.md`. A Debian backport request is the useful report — the user's call; don't post without asking.

## Lessons to put in every phase brief

1. Tests run offscreen (`conftest.py`), must be **silent** (`player_options={"ao": "null"}`), and never touch real drives or `~`: `XDG_DATA_HOME`, `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` are pointed at temp dirs by conftest; drives are faked with seams (`is_mount_point=`, `app_location=`, `ask_to_create_library=`, `ask_to_restore_library=`, `backup_root=`, `folder_picker=`).
2. Create mpv players only via `video.new_engine()` (sets `LC_NUMERIC=C`; libmpv otherwise returns NULL → segfault).
3. `gui_thread_gc` disables automatic GC and collects on a GUI-thread timer — Python's GC running on mpv's event thread freed Qt widgets mid-paint (segfault). Keep it in force for any new top-level window.
4. **Offscreen hides real bugs.** Every phase found bugs only on the native display (clipped text, widgets behind video, modal timing, fullscreen loss, popups replacing whole text). Native check recipe: throwaway exFAT image (`hdiutil create -size 64m -fs ExFAT -volname MTFAKE …; hdiutil attach`), scratch `XDG_*` dirs, drive the real `main()` from a scratch script outside the repo, `screencapture -x main.png second.png`. The user's main display is 2560x1080; a rotated 1080x1920 second display often hosts the app.
5. Scratch scripts must create a `QGuiApplication` before drawing text and must check a widget exists before `QTest.keyClicks` — otherwise Python aborts and the user gets a crash dialog. Reproduce crashes headlessly, never on screen.
6. Capture only with the app frontmost; delete captures showing the user's other windows (has happened: browser, meeting screen-share).
7. Never write to `/Volumes/MEDIATAGGER` (the app stick) from agents. Don't touch `spikes/` from phase agents; the orchestrator owns it.
8. **`deleteLater` never runs between offscreen test steps** unless the test lets the event loop process deferred deletions — the Esc bug only showed on the Pi because of this. Tests of teardown/re-entry must flush `QEvent.Type.DeferredDelete`.
9. Native-check scripts: answer the create-library modal in one `QTimer` callback and continue from a *separate* timer (continuing inside the modal's callback fakes "No library open" and a hang on exit); send keys to `QApplication.activePopupWidget()` when a completer popup is open (that's where real keystrokes go); prefer `window.grab()` over `screencapture` (captures only the app). Completer popups are separate windows — check them by geometry/visibility, not in `grab()`.

## Environment

- Mac (Apple Silicon), Python 3.13 via `uv`, Homebrew `mpv`/`ffmpeg`. Run: `uv run mediatagger [path]`.
- Linux check VM (UTM, Debian 13 arm64): `ssh -i ~/.ssh/mediatagger_vm me@192.168.65.2`. Software GL only — never judge visuals there. It sleeps; ask the user to wake it.
- Raspberry Pi 4 (Pi OS trixie, user `rb`): **no network**. Reached only by the user carrying the `MEDIATAGGER` exFAT stick. libmpv2 is installed (via `setup-pi.sh` from the stick). HEVC is hardware-decoded (`hwdec=drm`).

## The stick (`MEDIATAGGER`)

- Layout: `mediatagger/app/` (precompiled code), `mediatagger/lib-linux-aarch64-cp313/` (PySide6-Essentials 6.12, python-mpv), `run-app.sh` (sets `PYTHONDONTWRITEBYTECODE=1`), `setup-pi.sh`, `debs/`, `samples/` (awkward test media).
- Refresh it from the Mac with `sh spikes/drive/push-app.sh /Volumes/MEDIATAGGER` — **from a clean checkout of a validated commit** (use `git worktree add --detach <dir> <commit>` if HEAD is mid-phase), then clean `._*` files and eject.
- Rule from the user: **the app's own drive is never written while the app runs.** Tags live on the media drive (`.mediatagger/tags.db`); backups and state live on the Pi (`~/.local/share`, `~/.config`).
- Currently on the stick: Phase 8 build `ff64cc3` (validated), `PI-CHECKLIST.txt`, `mediatagger/diag-video.sh` (run, results in `results/diag-video.txt`), `mediatagger/diag-video2.{sh,py}` (run, results in `results/`), `mediatagger/diag-video3.{sh,py}` (run; results and per-variant `.err` files in `results/`). `results/` holds the user's first Pi run (15 logs + `findings.txt`).

## Open with the user

- The video-crash cause is found (see its section); the fix is built (Phase 9b) and checked on the Mac. 9a + 9b validated on the Mac (611 tests, native checks); next is the Pi run.
- First Pi run (2026-10-11): browsing, images, videos, tagging, persistence and autocomplete all worked on the Pi. Their findings: video crash (above), drive name irrelevant, no seeking, no video progress, want windowed mode — all but the crash are in Phase 9a.
- Decisions made by the orchestrator that the user may overrule: no libraries on a computer's own disk; declining "create library" lasts the session; random drive id; Esc quits from the grid; inherited tags computed on read (never copied to files); grid badge and prompt show own tags only.
- Crash dialogs: `Python-2026-10-11-203709.ips` (SIGABRT in `QTest.keyClicks`) was the orchestrator's own native-check script, not the app. Phase 8's two real crashes (Qt object freed on a worker thread; PySide lazy type creation racing in workers) are fixed with regression tests. The user can silence dialogs with `defaults write com.apple.CrashReporter DialogType none` (their call).
