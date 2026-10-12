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
| 9a Pi fixes & video controls | **in progress — paused at 16/38** (HEAD `2be4f88`, 573 tests). Resume with `/tdd-deliver` (it resumes the TODO list). See "Phase 9a — resume here" below |
| 10 Search | not started |
| 11 Run from the drive on the Pi | not started (spike tooling exists in `spikes/drive/`) |

Code: `src/mediatagger/` — `window.py` (top-level, switches grid ⇄ viewer), `grid.py`, `viewer.py`, `tag_prompt.py` (the `t` prompt, shared by grid and viewer), `status_bar.py`, `drive_session.py` (library open/create/restore/backup), `library.py` (SQLite, schema v2), `backup.py`, `state.py` (last folder, `$XDG_CONFIG_HOME`), `folder.py`, `slideshow.py`, `thumbnails.py` (image/video/folder thumbnails, `ffmpeg`/`ffprobe`), `thumbnail_cache.py`, `thumbnail_scheduler.py` (3 workers + prefetch), `folder_thumbnails.py` (a folder's thumbnails for its grid), `video.py` + `mpv_surface.py` (libmpv render API), `video_controls.py` (Phase 9a: video progress bar — in progress), `gui_thread_gc.py`. Tests are co-located (`test_*.py`). Open structural debt is in `BACKLOG.md`.

## How the work has been run

- One Opus subagent per PLAN phase, strictly in order, each invoking the `tdd-deliver` skill (falling back to `tdd-supervise`). The orchestrator (main session) writes a detailed brief, monitors progress, then **validates** before starting the next phase:
  - full suite twice (`.tdd-test-cmd`; ~340+ tests, ~1 min),
  - read the diff of production code for scope creep and structure,
  - native check on the real screen (see below),
  - no new crash reports from this project,
  - send the agent back with a numbered fix list if anything is off.
- Progress is relayed to the user in chat from a `Monitor` that polls `git log`, `TODO.md` checkbox counts, `~/Library/Logs/DiagnosticReports/Python-*.ips` and `/Volumes/MEDIATAGGER`. Monitors expire every 30 min; re-arm.
- The user asked for progress to be printed in the conversation and for questions only when a decision is genuinely theirs.

## Phase 9a — resume here

Spec: PLAN.md "Phase 9a". The user decided every behaviour in it (2026-10-11): status bar shows only problems (no `Library: <drive>`), video progress bar with `elapsed / total` that auto-hides after ~3 s, `↑`/`↓` ±10 s plus `0`–`9` → 0–90 %, start windowed (≈80 % of the screen, geometry remembered in `state.json`), `f` toggles fullscreen.

- **Done (16):** Esc-back-to-grid fix (`FolderThumbnails.stop` idempotent, regression test flushes deferred deletes), relative launch path, refused seek caught, status bar refreshes on every way into a folder, `t`/`Enter` in an empty folder, `Library: <drive>` label removed (10 tests migrated, none deleted), progress bar skeleton (`video_controls.ProgressBar`, shows `0:00 / total`, hidden for images/unplayable clips).
- **Next unchecked item:** "While a video plays, the progress bar's elapsed time advances".
- **Do first when resuming:** `viewer.py` grew 270 → 280 lines against the rule. Move the progress bar's show/hide decisions into `video_controls.py` so the viewer wires it once, and keep the remaining progress, seek-feedback and digit-key logic there. Target ≤ 270 (the image-decoding helpers used only by the viewer could also move out).
- **Known contradictions ahead:** windowed start breaks 2 `test_main.py` tests that expect fullscreen; geometry-on-close breaks 1 `test_window_state.py` test expecting no `state.json`; the standalone `Viewer` still forces fullscreen (`test_viewer.py:202`) — decide whether it should follow the window.
- **Loose ends:** `ThumbnailScheduler.shut_down` itself is not guarded against a second call (only `FolderThumbnails.stop` is); `DESIGN.md:146` still describes the `Library:` label (docs-sync hasn't run); flaky `test_main.py::…shows_a_generated_thumbnail_on_an_image_tile_after_esc` failed once in 3 cycles under heavy machine load, never reproduced idle.
- **After the TODO list:** the closing loops (refactor/test-quality/complexity passes, docs-sync, archive, backlog audit) haven't run for 9a. Then validate as usual (suite twice, diff, native check: progress bar over black and bright video, fade timing, window start on 2560x1080 and the rotated 1080x1920 display, `f`), push to the stick, and send the user to the Pi.

## Video crash on the Pi — root cause found, fix planned (not yet built)

- Symptom (first Pi run, build `ff64cc3`): video plays ~30–40 s, then `Too many open files` → Wayland connection dies → app exits. `diag-video.sh`: +1 `anon_inode:sync_file` fd per frame, regardless of mpv decode options or Wayland/XWayland. `diag-video3.sh`: the real app leaks (~15/s, fullscreen and windowed); the diag replicas didn't — but they never actually rendered per frame (their `QTimer.singleShot` from mpv's thread never fired), so diag2/diag3 replica rows prove nothing about mpv-in-Qt. Qt GL redraw alone and mpv in its own window (`vo=gpu`, `wid`) genuinely don't leak.
- **Root cause (mpv 0.40 bug, render API + OpenGL):** `video/out/opengl/libmpv_gl.c` `done_frame` → `ra_gl_ctx_submit_frame` (`context.c:235`) creates a `glFenceSync` after every rendered frame and appends it to `vsync_fences`; those are only deleted in `ra_gl_ctx_swap_buffers`, which the libmpv render path never calls. So one GL fence leaks per frame on every platform; on the Pi's Mesa v3d each fence holds a `sync_file` fd → fd exhaustion. Regressed in 0.40.0; fixed on mpv master by f74adc4 (2026-01-22, mpv#17217) but in no release yet (latest v0.41.0) nor any Debian package.
- **Proven on the Mac (2026-10-12):** a QOpenGLWidget + render-API test redrawn per frame (like `MpvSurface`) had 443 live fences after 15 s (1 per frame, never deleted); with the workaround, 0 live fences and playback unaffected (30 fps). Script: `spikes/fence_check_mac.py` (wraps `glFenceSync`/`glDeleteSync` through the proc-address callback and counts).
- **Fix (small, own phase "9b", after or alongside 9a):** in `mpv_surface.MpvSurface.initializeGL`, the `get_proc_address` callback returns, for `glFenceSync`, a ctypes stub that returns `NULL` (mpv skips storing a null fence: `if (fence)`); keep a reference to the stub. Also set `vd-lavc-dr=no` in the viewer's player options, because mpv's only other fence use (`ra_gl.c` host-mapped PBOs, used by direct rendering) would otherwise treat buffers as immediately reusable. Do **not** simply hide `glFenceSync` — `GL_ARB_sync` is core in GLES 3 (the Pi) and mpv refuses to init if a core function is missing (`common.c` `must_exist`). Tests: the resolver returns a stub for `glFenceSync` that returns 0 and passes other names through; the viewer's engine runs with `vd-lavc-dr=no`. Native check: count live fences in the real app on the Mac (wrap as in `fence_check_mac.py`) → flat; then a Pi run counting `sync_file` fds of the app (`diag-video3.sh`'s app rows) → flat, and play a video for minutes.
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

- The video-crash cause is found (see its section); the fix is planned as Phase 9b. Next Pi trip: after 9a + 9b are validated.
- First Pi run (2026-10-11): browsing, images, videos, tagging, persistence and autocomplete all worked on the Pi. Their findings: video crash (above), drive name irrelevant, no seeking, no video progress, want windowed mode — all but the crash are in Phase 9a.
- Decisions made by the orchestrator that the user may overrule: no libraries on a computer's own disk; declining "create library" lasts the session; random drive id; Esc quits from the grid; inherited tags computed on read (never copied to files); grid badge and prompt show own tags only.
- Crash dialogs: `Python-2026-10-11-203709.ips` (SIGABRT in `QTest.keyClicks`) was the orchestrator's own native-check script, not the app. Phase 8's two real crashes (Qt object freed on a worker thread; PySide lazy type creation racing in workers) are fixed with regression tests. The user can silence dialogs with `defaults write com.apple.CrashReporter DialogType none` (their call).
