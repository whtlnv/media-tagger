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
| 8 Thumbnails | done, validated on the Mac (pending the Pi check) — includes video duration and folder-tile first-image previews |
| 9 Tag folders & inherited tags | **next** (`t` in the grid lives here) |
| 10 Search | not started |
| 11 Run from the drive on the Pi | not started (spike tooling exists in `spikes/drive/`) |

Code: `src/mediatagger/` — `window.py` (top-level, switches grid ⇄ viewer), `grid.py`, `viewer.py`, `status_bar.py`, `drive_session.py` (library open/create/restore/backup), `library.py` (SQLite, schema v2), `backup.py`, `state.py` (last folder, `$XDG_CONFIG_HOME`), `folder.py`, `slideshow.py`, `thumbnails.py` (image/video/folder thumbnails, `ffmpeg`/`ffprobe`), `thumbnail_cache.py`, `thumbnail_scheduler.py` (3 workers + prefetch), `folder_thumbnails.py` (a folder's thumbnails for its grid), `video.py` + `mpv_surface.py` (libmpv render API), `gui_thread_gc.py`. Tests are co-located (`test_*.py`). Open structural debt is in `BACKLOG.md`.

## How the work has been run

- One Opus subagent per PLAN phase, strictly in order, each invoking the `tdd-deliver` skill (falling back to `tdd-supervise`). The orchestrator (main session) writes a detailed brief, monitors progress, then **validates** before starting the next phase:
  - full suite twice (`.tdd-test-cmd`; ~340+ tests, ~1 min),
  - read the diff of production code for scope creep and structure,
  - native check on the real screen (see below),
  - no new crash reports from this project,
  - send the agent back with a numbered fix list if anything is off.
- Progress is relayed to the user in chat from a `Monitor` that polls `git log`, `TODO.md` checkbox counts, `~/Library/Logs/DiagnosticReports/Python-*.ips` and `/Volumes/MEDIATAGGER`. Monitors expire every 30 min; re-arm.
- The user asked for progress to be printed in the conversation and for questions only when a decision is genuinely theirs.

## Carry into Phase 8 (from Phase 7 review)

- Tiles look sparse (tiny glyphs, badges at cell edges) — Phase 8's thumbnails should redo the tile look; check it on the native display.
- On relaunch, a single tile was once drawn one row down from the top — uninvestigated.
- The selected item's tags are fetched with one query per cursor move — fine now, cache if it shows on the Pi.
- Incident: before conftest pinned `XDG_CONFIG_HOME`, one test run wrote `~/.config/mediatagger/state.json` in the real home; it was deleted. Any new on-disk location needs a conftest guard **before** the first test that writes it.

## Lessons to put in every phase brief

1. Tests run offscreen (`conftest.py`), must be **silent** (`player_options={"ao": "null"}`), and never touch real drives or `~`: `XDG_DATA_HOME`, `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` are pointed at temp dirs by conftest; drives are faked with seams (`is_mount_point=`, `app_location=`, `ask_to_create_library=`, `ask_to_restore_library=`, `backup_root=`, `folder_picker=`).
2. Create mpv players only via `video.new_engine()` (sets `LC_NUMERIC=C`; libmpv otherwise returns NULL → segfault).
3. `gui_thread_gc` disables automatic GC and collects on a GUI-thread timer — Python's GC running on mpv's event thread freed Qt widgets mid-paint (segfault). Keep it in force for any new top-level window.
4. **Offscreen hides real bugs.** Every phase found bugs only on the native display (clipped text, widgets behind video, modal timing, fullscreen loss, popups replacing whole text). Native check recipe: throwaway exFAT image (`hdiutil create -size 64m -fs ExFAT -volname MTFAKE …; hdiutil attach`), scratch `XDG_*` dirs, drive the real `main()` from a scratch script outside the repo, `screencapture -x main.png second.png`. The user's main display is 2560x1080; a rotated 1080x1920 second display often hosts the app.
5. Scratch scripts must create a `QGuiApplication` before drawing text and must check a widget exists before `QTest.keyClicks` — otherwise Python aborts and the user gets a crash dialog. Reproduce crashes headlessly, never on screen.
6. Capture only with the app frontmost; delete captures showing the user's other windows (has happened: browser, meeting screen-share).
7. Never write to `/Volumes/MEDIATAGGER` (the app stick) from agents. Don't touch `spikes/` from phase agents; the orchestrator owns it.

## Environment

- Mac (Apple Silicon), Python 3.13 via `uv`, Homebrew `mpv`/`ffmpeg`. Run: `uv run mediatagger [path]`.
- Linux check VM (UTM, Debian 13 arm64): `ssh -i ~/.ssh/mediatagger_vm me@192.168.65.2`. Software GL only — never judge visuals there. It sleeps; ask the user to wake it.
- Raspberry Pi 4 (Pi OS trixie, user `rb`): **no network**. Reached only by the user carrying the `MEDIATAGGER` exFAT stick. libmpv2 is installed (via `setup-pi.sh` from the stick). HEVC is hardware-decoded (`hwdec=drm`).

## The stick (`MEDIATAGGER`)

- Layout: `mediatagger/app/` (precompiled code), `mediatagger/lib-linux-aarch64-cp313/` (PySide6-Essentials 6.12, python-mpv), `run-app.sh` (sets `PYTHONDONTWRITEBYTECODE=1`), `setup-pi.sh`, `debs/`, `samples/` (awkward test media).
- Refresh it from the Mac with `sh spikes/drive/push-app.sh /Volumes/MEDIATAGGER` — **from a clean checkout of a validated commit** (use `git worktree add --detach <dir> <commit>` if HEAD is mid-phase), then clean `._*` files and eject.
- Rule from the user: **the app's own drive is never written while the app runs.** Tags live on the media drive (`.mediatagger/tags.db`); backups and state live on the Pi (`~/.local/share`, `~/.config`).
- Currently on the stick: Phase 5 build `a484ab2` (autocomplete). Phases 6–7 not yet loaded.

## Open with the user

- **Pi test results are still outstanding.** The user hasn't reported back on the checklist (photos/videos/4K HEVC/sound/speed/tagging on a media USB drive on the Pi). Ask for `results*.txt` on the stick or notes in chat when they return; fix viewer issues before or between phases.
- Decisions made by the orchestrator that the user may overrule: no libraries on a computer's own disk; declining "create library" lasts the session; random drive id; Esc quits from the grid; grid tiles were glyphs in Phase 7 (thumbnails in Phase 8).
- Crash dialogs: several were caused by agent scratch scripts or deliberate reproduction (not the app); one real bug (GC thread) was found and fixed. The user can silence the dialogs with `defaults write com.apple.CrashReporter DialogType none` (their call).
