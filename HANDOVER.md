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
| 11 Run from the drive on the Pi | done, validated on the Mac + VM (`abe5ae3`, 738 tests); Pi run pending — see "Phase 11 — done" |
| 12 Fixes from the second Pi run | done, validated on the Mac (`cf4db51`, 769 tests); Pi run pending — see "Phase 12 — done" |
| 13 Video speed, rotation, show controls | done, validated on the Mac (`21e6968`, 789 tests); Pi run pending |
| 14 Zoom | done, validated on the Mac (`78f1a39`, 813 tests); Pi run pending |
| 15 Key cheat sheet | done, validated on the Mac (`83868f5`, 835 tests); Pi run pending |
| 16 Required tags | done, validated on the Mac (`a6efa62`, 858 tests); Pi run pending |
| 17 Grid filters | done, validated on the Mac (`0b28e39`, 908 tests); Pi run pending |
| 18 Video chapters | done, validated on the Mac (`1c4d945`, 982 tests); Pi run pending |

Code: `src/mediatagger/` — `window.py` (top-level, switches grid ⇄ viewer), `grid.py`, `grid_filter.py` (the grids' shared filter and its button), `viewer.py`, `tag_prompt.py` (the `t` prompt, shared by grid and viewer), `status_bar.py`, `drive_session.py` (library open/create/restore/backup), `drive_config.py` (the drive's `mediatagger_config.json`: required tag roots), `library.py` (SQLite, schema v3: tags and chapter moments), `backup.py`, `state.py` (last folder, geometry, recent searches; `$XDG_CONFIG_HOME`), `search.py` (query matching), `search_bar.py` (the `/` box and its `↑`/`↓` history), `folder.py`, `slideshow.py`, `thumbnails.py` (image/video/folder thumbnails, `ffmpeg`/`ffprobe`), `thumbnail_cache.py`, `thumbnail_scheduler.py` (3 workers + prefetch), `folder_thumbnails.py` (a folder's thumbnails for its grid), `video.py` + `mpv_surface.py` (libmpv render API), `video_controls.py` (video progress bar), `chapters.py` + `chapter_list.py` (the viewer's `c`, `.`/`,` and `l` chapters), `zoom.py` (mouse-wheel zoom for images and mpv), `gui_thread_gc.py`. Tests are co-located (`test_*.py`). Open structural debt is in `BACKLOG.md`.

## How the work has been run

- One Opus subagent per PLAN phase, strictly in order, each invoking the `tdd-deliver` skill (falling back to `tdd-supervise`). The orchestrator (main session) writes a detailed brief, monitors progress, then **validates** before starting the next phase:
  - full suite twice (`.tdd-test-cmd`; ~340+ tests, ~1 min),
  - read the diff of production code for scope creep and structure,
  - native check on the real screen (see below),
  - no new crash reports from this project,
  - send the agent back with a numbered fix list if anything is off.
- Progress is relayed to the user in chat from a `Monitor` that polls `git log`, `TODO.md` checkbox counts, `~/Library/Logs/DiagnosticReports/Python-*.ips` and `/Volumes/MEDIATAGGER`. Monitors expire every 30 min; re-arm.
- The user asked for progress to be printed in the conversation and for questions only when a decision is genuinely theirs.

## Phase 18 — done

Chapters = tags at moments (`moments(item_id, tag_id, tenths)`, schema 3). `chapters.py` watches the viewer's keys: `c` (tag prompt, moment captured at the key press, video keeps playing), `.`/`,` jumps (bar shows `tag · m:ss / m:ss`), `l` list overlay above the mpv surface (↑/↓, Enter jumps, Backspace deletes, Esc closes; with the cheat sheet shown the first Esc hides the sheet). Amber ticks on the progress bar; `⏱ n` tile badge after the tag count. The v1/v2 → v3 upgrade runs in one `BEGIN IMMEDIATE` transaction, only adds, leaves read-only drives at their schema. Orchestrator check: suite twice (982); a v2 library created by the previous build (`58f9105`) opened by the new one: items/tags/item_tags identical, drive id kept, schema 3; the same library read-only: stays 2, tags read, file byte-identical; native: `c` while playing, `.` label, `l` list over video, ticks, badge.

- **Important for the Pi:** once a drive is opened by this build it is schema 3; an older build still reads its tags but ignores chapters and may leave stray (invisible) moment rows when it removes tags.
- 2026-10-15 23:21 crash report was the orchestrator's own check script (`QTest.keyClick(None)`), not the app.

## Phase 17 — done

`grid_filter.GridFilter` (one per Window, not saved) + `FilterButton` (40 px disc, bottom-right of the tile area, mouse only, never focused): With tags / No tags use OWN tags (what the badge counts); Missing tags = files with a ✕ mark, offered only with required roots (or while active). File rows are hidden in place; folder and ❓ tiles stay; applies to folder and results grids; tagging hides a no-longer-matching file at once; cursor skips hidden tiles; Enter starts a slideshow over only the shown files. Orchestrator check: suite twice (908), native: button off/on look, menu with checkmarks, Missing tags and With tags filter and pack tiles, choosing the active one again shows all.

- **Known (BACKLOG):** with `i` on, opening from a filtered grid drops the info overlay until `i` again; prefetch still makes thumbnails for hidden files.

## Phase 16 — done

`drive_config.required_roots(drive)` reads `<drive>/mediatagger_config.json` (`requiredRoots`, read only) whenever the session opens a drive; a bad file shows `mediatagger_config.json can't be read — no tiles marked` in its own status-bar label. File tiles (folder grids and search results, only with a library open) show `✕<n>` left of the tag badge, from bulk reads (`Library.own_tags_in`, `tagged_items`); `Grid.show_new_tags` re-reads counts and marks after every save (also fixed stale counts in results after a results slideshow). Roots match case-sensitively as written. Orchestrator check: suite twice (858), native: badges at 200 px and smallest size, `t` updates ✕2→✕1 at once, broken config message, drive gains no files.

- **Pi to check:** 5,000-file folder open time with roots; tag-save time in a big folder (BACKLOG: whole-grid re-read per save).

## Phase 15 — done

`h` toggles `cheat_sheet.CheatSheet`, a mouse-transparent, never-focused widget over the whole Window, raised above the stack (so above the mpv surface) that paints a centred translucent panel of the current screen's keys (`GRID_KEYS`, `VIEWER_KEYS`, `LAUNCH_KEYS`, pinned against DESIGN.md's tables). Esc while shown only hides it; other keys pass through; `h` in the tag prompt / search bar types. Shown state in `state.json` (`cheat_sheet`). First delivered as a background behind the media per the original spec; the native check showed tiles and pictures hid it, and the user chose (2026-10-15) a dim overlay instead — reworked in `f61933c..83868f5`. Orchestrator check: suite twice (835), native: panel readable over the grid and a playing video, keys switch grid ⇄ viewer, Esc hides then goes back. The automated quality loops and `/backlog-audit` were skipped for the rework.

## Phase 14 — done

`zoom.Zoom` (level 1–3, pan in mpv `video-pan` units): images are drawn into `Zoom.shown(...)`, videos get `video-zoom = log2(level)` + `video-pan-x/y`; 10 points per wheel notch; a zoomed picture never shows black inside the window; back at 100 % it is centred; `r` keeps zoom/pan; the first notch re-decodes a photo at up to 3× the window. `MpvSurface` is transparent to mouse events so the wheel over video reaches the viewer. Ran mostly by hand (headless sessions hit a usage limit): the automated quality loops and `/backlog-audit` were not run this phase. Orchestrator check: suite twice (813; one load-induced flake of a 3 s quit test, passes 5/5 alone), native: image zoom anchored at the pointer and clamped, video zoom via wheel over the surface (renders after the clip has started), `r` while zoomed, next item resets.

- **Known (BACKLOG):** after a resize / `f` / `r` on a zoomed, edge-panned picture, black can show until the next notch; the 3× decode of a 12 MP photo (~48 MB) is unmeasured on the Pi.
- **Pi to check:** zoomed hwdec HEVC smooth and `sync_file` flat; first-notch decode time/memory; wheel reaches the viewer under Wayland.

## Phase 13 — done

`]`/`[` step mpv `speed` through `video.SPEEDS` (0.25–8×, shown as ` · 2×` on the bar when not 1×), `r` adds 90° to `video-rotate`, `v` only wakes the bar; each new video starts at 0° and 1×. The rotated fit is pinned by `test_video_fit.py` (headless CGL + libmpv GL render, pixel readback; macOS only). Orchestrator native check: landscape clip rotated fills the height, whole, pillarboxed; speed label and limits; reset on next/back; the keys type into the tag prompt. Pi to check: rotation with hwdec HEVC stays smooth, 4–8× playback, `sync_file` flat while rotated.

## Phase 12 — done

From the user's Pi run of 3bd9a25 (`spikes/drive/pi-results-2026-10-14/`). Root causes: `o` was only handled on the launch screen (the grid's QListView keyboard search swallowed it); grid drops never arrived on any platform because `QAbstractItemView.dragMoveEvent` refused the move (old tests sent enter+drop without a move); the quit hang was the grid's thumbnail workers (Python waits for ThreadPoolExecutor threads at exit) — `closeEvent` now stops every grid's generation; `qt.qpa.wayland.textinput.warning` silenced in `main()` (a user's `QT_LOGGING_RULES` still wins); progress bar backdrop removed, text white with a 1-px dark edge, a dark hairline above the filled track. Orchestrator check: suite twice (769), diff review, native: bar over black and white video (over white only the hairline and edged text show — user to judge), quit mid-video exits at once.

- **Not checked natively:** a real Finder/file-manager drag (offscreen tests send the full enter→move→drop sequence); the native folder picker.
- **Known:** quitting still waits for a worker's file in progress (ffmpeg timeout 15 s) — BACKLOG.
- 2 crash reports (2026-10-14 03:32) were a red test step calling `QTest.keyClick(None, …)`; not the app.

## Phase 11 — done

Product scripts in `drive/` (tests co-located, external commands faked on PATH): `build-drive.sh` (VM: packages pinned to `uv.lock`, all of `~/aptpi`'s .debs + index, then `update-drive.sh`), `update-drive.sh` (Mac or VM: app + scripts only; replaces `spikes/drive/push-app.sh`), `run.sh`, `setup-pi.sh` (libmpv2 only if missing, then the menu entry), `check-video-leak.sh`. Orchestrator check: suite twice (738), script review; the agent ran the build in the VM into a scratch folder, `setup-pi.sh` with apt in simulate mode, and an update onto a scratch exFAT image on the Mac (found and fixed `._*.py` breaking compileall).

- **Stick as of 2026-10-14:** build `3bd9a25` pushed with the old `spikes/drive/push-app.sh` (old layout: `run-app.sh`, old `setup-pi.sh`), with `PI-CHECKLIST.txt` for 9a/9b/10. Old spike files moved to `results/old-files-2026-10-13/`. Next update: `sh drive/update-drive.sh /Volumes/MEDIATAGGER` from a clean worktree, then `sh setup-pi.sh` once on the Pi for the menu entry.
- **Pi-only checks pending:** `setup-pi.sh` with real sudo/apt offline; the menu entry starts the app; `build-drive.sh` onto the real stick via VM passthrough.
- **Known:** an update whose precompile fails leaves the drive without `app/mediatagger` until rerun; a failed install leaves `setup-pi.sh`'s temp folder.

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
- Refresh it from the Mac with `sh drive/update-drive.sh /Volumes/MEDIATAGGER` — **from a clean checkout of a validated commit** (use `git worktree add --detach <dir> <commit>` if HEAD is mid-phase), then eject (the script removes `._*` files under `mediatagger/` itself; any elsewhere on the stick are left alone).
- Rule from the user: **the app's own drive is never written while the app runs.** Tags live on the media drive (`.mediatagger/tags.db`); backups and state live on the Pi (`~/.local/share`, `~/.config`).
- Currently on the stick: Phase 8 build `ff64cc3` (validated), `PI-CHECKLIST.txt`, `mediatagger/diag-video.sh` (run, results in `results/diag-video.txt`), `mediatagger/diag-video2.{sh,py}` (run, results in `results/`), `mediatagger/diag-video3.{sh,py}` (run; results and per-variant `.err` files in `results/`). `results/` holds the user's first Pi run (15 logs + `findings.txt`).

## Open with the user

- The video-crash cause is found (see its section); the fix is built (Phase 9b) and checked on the Mac. 9a + 9b validated on the Mac (611 tests, native checks); next is the Pi run.
- First Pi run (2026-10-11): browsing, images, videos, tagging, persistence and autocomplete all worked on the Pi. Their findings: video crash (above), drive name irrelevant, no seeking, no video progress, want windowed mode — all but the crash are in Phase 9a.
- Decisions made by the orchestrator that the user may overrule: no libraries on a computer's own disk; declining "create library" lasts the session; random drive id; Esc quits from the grid; inherited tags computed on read (never copied to files); grid badge and prompt show own tags only.
- Crash dialogs: `Python-2026-10-11-203709.ips` (SIGABRT in `QTest.keyClicks`) was the orchestrator's own native-check script, not the app. Phase 8's two real crashes (Qt object freed on a worker thread; PySide lazy type creation racing in workers) are fixed with regression tests. The user can silence dialogs with `defaults write com.apple.CrashReporter DialogType none` (their call).
