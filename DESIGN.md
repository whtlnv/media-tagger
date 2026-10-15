# MediaTagger — Design

A keyboard-first media viewer and tagger for a Raspberry Pi 4 desktop, developed on an Apple Silicon Mac.
Decisions below were settled in a design interview (2026-10-08). `PLAN.md` holds the delivery phases.

## Platform

| | |
|---|---|
| Target | Raspberry Pi 4, Raspberry Pi OS (Debian 13 trixie, aarch64, Wayland desktop), monitor + keyboard + mouse |
| Dev | macOS arm64 (native), plus an arm64 Debian 13 VM (UTM/OrbStack) for Linux checks |
| Language | Python 3.13 (matches trixie), managed with `uv` |
| UI | PySide6 (Qt 6) |
| Video | libmpv via `python-mpv`, embedded with mpv's render API in a `QOpenGLWidget` (works on Wayland) |
| Images | Qt `QImageReader` with scaled decoding; HEIC only if a HEIC plugin is installed, otherwise an "unsupported" tile |
| Thumbnails | Qt for images, `ffmpeg` for video frames |
| Storage | SQLite (stdlib `sqlite3`) |
| Tests | pytest + pytest-qt, co-located with source, TDD |

Why not Go: Go's GUI options can't play AVI/MPG with hardware decode (Fyne has no video; gotk4 is slow to build and fiddly with libmpv).
Why not web/Electron/Wails: browsers can't play AVI/MPEG-2/DivX, and dropped folders don't expose real paths.

## Naming

`mediatagger` everywhere: command `mediatagger`, package `mediatagger/`, drive folder `.mediatagger/`, menu entry "MediaTagger".

## The library (one USB drive)

- The **library root** is the mount point of the drive containing whatever was opened (walk up from the path until a mount point).
- Library data lives on the drive: `<root>/.mediatagger/tags.db`. Paths are stored **relative to the root**, so the same drive works on the Mac and the Pi.
- First time on a drive: ask "Create a tag library on <drive>?" before writing anything. A declined drive is not asked again for the rest of the session.
- The system disk (mount point `/`) never holds a library: media there is viewing only.
- Read-only drive: browsing and viewing work; tagging is disabled, with a banner saying so.
- Each library has a unique `drive_id` stored in its DB. One drive at a time.
- **Only tagged items are stored.** Untagged directories are never indexed. Browsing reads the filesystem live.
- A tagged path that no longer exists shows as a **missing** tile in results; its tags can be removed from there. No rename/move tracking.

### Backups

When a library opens, before switching to another drive, and on exit, copy `tags.db` with the SQLite backup API to `$XDG_DATA_HOME/mediatagger/backups/<drive_id>/` (default `~/.local/share/mediatagger/backups/<drive_id>/`), keeping the last 10; an unchanged DB writes no new backup. If the drive's DB is missing or corrupt, offer to restore the latest backup for a drive of the same name, keeping the damaged file as `.mediatagger/tags.db.damaged-<timestamp>`. A read-only drive is not offered a restore.

### Thumbnail cache

On the Pi, not the drive: `$XDG_CACHE_HOME/mediatagger/<drive_id>/thumbs.db` (default `~/.cache/mediatagger/<drive_id>/thumbs.db`; thumbnails as blobs in one SQLite file). Keyed by relative path + size + mtime, so each is generated once and regenerated only when the file changes; a file that yields no thumbnail is not retried until it changes. With no library, or when that location falls on the app's own drive or the drive being viewed, thumbnails are kept in memory for the session only.

## Tags

- Lowercased, trimmed. Hyphens join words (`day-at-beach`; typed spaces inside one tag are not possible because space separates tags).
- Colons namespace tags, any depth: `people:ana`, `place:mexico:cancun`. Stored whole, as plain strings.
- Tags can be on **files** or **directories**.
- **Inheritance:** an item's effective tags = its own tags ∪ the tags of every ancestor directory.

### Tag prompt (`t`)

- Shows the item's current own tags.
- `beach family` adds both; `-sunset` removes `sunset`.
- `Enter` saves the entry; `Esc` closes the prompt without changing tags.
- Autocomplete over existing tags, most used first; typing `people:` lists all `people:*` tags.
  A word starting with `-` suggests the item's own tags; otherwise tags the item already has, and words already entered, aren't suggested.
  With the suggestion popup open, `↓`/`↑` move the highlight, `Tab` or `Enter` completes the last word with the highlighted tag (without saving), and `Esc` closes only the popup.
- If saving fails, the prompt stays open with its text and the status bar says `Couldn't save tags — is the drive still connected?`.

## Search

Syntax:

| Input | Meaning |
|---|---|
| `beach family` | AND |
| `-sunset` | NOT |
| `beach\|pool` | OR |
| `people:` | prefix: any tag starting with `people:` |
| `people:ana` | exact |

Rules:

1. Candidates are tagged items only (by construction nothing else can surface).
2. An item matches if its **effective** tags satisfy the query.
3. **Collapse:** if a matching item has a matching ancestor directory, show only the top-most matching directory.
4. Opening a directory from results shows that folder normally (all contents, unfiltered).
5. `Enter` on a file in results starts a slideshow **over the result list**, starting at that file.

Results show under a `Search: <query>` breadcrumb; a result whose path no longer exists is drawn as a missing tile (❓ and its name).

`↑`/`↓` in the search box step through the 50 most recent searches, remembered in `state.json`.

## Media

- Images: jpg, jpeg, png, webp, bmp, tif, tiff, heic.
- Video (played by mpv): mp4, mov, avi, mpg, mpeg, mkv, m4v, wmv, 3gp, **gif**.
- Ignore hidden files and macOS litter on exFAT (`._*` AppleDouble files, `.DS_Store`, `.Spotlight-V100`, `.fseventsd`, `.Trashes`).
- Order: natural filename sort ignoring letter case (`IMG_2` before `IMG_10`, `img_3` between them), folders first in the grid.
- Images honour their EXIF orientation (sideways phone photos display upright).
- Slideshow covers the current folder only (non-recursive).

## Screens and keys

### Launch

- If the drive from last session is mounted: reopen the last folder in the grid. The last folder shown is remembered in `$XDG_CONFIG_HOME/mediatagger/state.json` (default `~/.config/mediatagger/`), never written to the app's own drive or the drive being viewed.
- The window opens at the size and position remembered in `state.json` when it last closed; with none remembered, not fullscreen, at about 80 % of the available screen, centred.
- The key cheat sheet (`h`) starts shown or hidden as remembered in `state.json`; with nothing remembered, hidden.
- Otherwise: empty screen "Drop a folder or file here, or press o to open".

| Key | Action |
|---|---|
| `o` | open a folder (picker), as if dropped |
| `f` | toggle fullscreen |
| `Esc` | quit |
| `h` | show / hide the key cheat sheet behind the message |

### Drag & drop

- Drop a folder: start the slideshow of that folder.
- Drop a file: slideshow of its folder, starting at that file.
- A path that is missing or unreadable (or a file whose folder can't be listed) shows "Can't open <name>"; dropping or opening (`o`) another path still works.

### Viewer

| Key | Action |
|---|---|
| `Space` / `→` | next |
| `←` | previous |
| `t` | tag prompt |
| `i` | toggle info overlay (filename, position `233 / 1,204`) |
| `Esc` | back to grid, cursor on the current file |
| `f` | toggle fullscreen |
| `p` / `Enter` | play/pause (video) |
| `↑` / `↓` | seek ±10 s (video) |
| `0`–`9` | jump to 0 %–90 % of the video |
| `m` | mute |
| `]` / `[` | faster / slower (video): 0.25×–8×, stopping at the ends |
| `r` | turn 90° clockwise (video), still fitted whole to the screen |
| `v` | show the progress bar (video), nothing else |
| `o` | open a folder (picker), as if dropped |
| mouse wheel | zoom in (up) / out (down) about the point under the mouse: 100 %–300 % in steps of 10 points (images and videos) |
| `h` | show / hide the key cheat sheet behind the picture |

- Images fit to screen.
- The key cheat sheet (`h`) is drawn dimly in the black behind the picture; a video covers it, so over a video it shows nowhere.
- Zoom: the picture point under the mouse stays under it, except that a picture bigger than the window always covers it and a smaller one stays inside it (no black between picture and edge). Back at 100 % it is centred again. Every item opens at 100 %; `r` keeps the zoom. No zoom indicator.
- Video autoplays **with sound**, loops, at 1× and unrotated. Space never pauses.
- While a video plays, a progress bar (`1:23 / 4:56`, `0:00:05 / 1:02:03` from an hour, `1:23 / 4:56 · 1.25×` when not at 1×) sits along its bottom above the status bar; any key shows it, and it hides after 3 s without input.
- Tag overlay in a corner: own tags normal, inherited tags dimmed.
- Manual advance only.

### Grid

| Key | Action |
|---|---|
| arrows | move |
| `Enter` | open (slideshow from here, or enter folder) |
| `Backspace` | up a folder |
| `/` | focus search |
| `t` | tag selected item (file or folder) |
| `+` / `-` | tile size |
| `Esc` | quit; (in search) clear search, back to the folder |
| `f` | toggle fullscreen |
| `o` | open a folder (picker), as if dropped |
| `h` | show / hide the key cheat sheet behind the tiles |

- Tiles ~200 px: thumbnail (a large type glyph until it arrives, or when there is none), truncated filename, tag-count badge when the item has own tags.
- Video tiles: frame at ~10%, ▶ badge, duration.
- Folder tiles: first image directly inside (natural order); none there, no thumbnail.
- Selected item's own tags shown in the status bar, followed by its inherited tags dimmed.

### Status bar (always visible)

It says when there is no library (viewing only), says `Library on <drive> can't be opened — viewing only` when the drive's `tags.db` can't be opened, and on a read-only drive adds `Read-only — tags can't be saved`.

Pressing `t` where tags can't be saved (no library, declined, can't be opened, read-only, system disk, the app's own drive) briefly shows `Tags can't be saved here`.

Any background work is announced and its completion shown, e.g. `⟳ Generating thumbnails 132 / 1,204` → `✓ Thumbnails ready`, `⟳ Backing up database…` → `✓ Backed up`. Failures read `✗ Backup failed: <reason>` / `✗ Restore failed: <reason>`. Nothing runs silently.

Thumbnail generation: on demand for visible tiles (3 workers, newest request first), then background prefetch of the rest of the current folder.

## Install: runs from the USB drive

The Pi has **no internet** (Bluetooth only). The app **lives on a USB drive** and runs from it with the Pi's own Python 3.13. Development works the same way: the drive is passed through to the arm64 trixie VM (UTM USB passthrough), tested there, then unplugged and plugged into the Pi.

Drive: **exFAT**, readable and writable by macOS, the VM and the Pi with no extra drivers. The dev drive is an 8 GB stick labelled `MEDIATAGGER`.

exFAT has no symlinks and no Unix permissions, so **no virtualenv on the drive**:

```
<drive>/
  mediatagger/
    app/                     source (the mediatagger package)
    lib-linux-aarch64-cp313/ third-party packages, installed with `--target` (PySide6-Essentials, python-mpv…)
    debs/                    libmpv2 + the dependencies the Pi lacks
    run.sh                   PYTHONPATH=app:lib-… python3, runs mediatagger.main()  (started via `sh run.sh`, so no exec bit needed)
    setup-pi.sh              ONE-TIME: install debs/, add the "MediaTagger" .desktop menu entry pointing at run.sh
    check-video-leak.sh      Pi diagnostic: runs the app on a video, logs its open fds, copies the log to results/ after exit
  .mediatagger/              library data for media on this drive (tags.db), as per "The library"
  .metadata_never_index      stops Spotlight indexing the drive on the Mac
```

- The only thing installed on the Pi itself is **libmpv2**. It must be the Pi's own build so that it uses the Pi's ffmpeg (`+rpt1`, with HEVC hardware decode). The Pi already has ffmpeg, libxcb-cursor0 and python3-venv.
- `lib-linux-aarch64-cp313/` and `debs/` are populated **in the VM** (same OS and architecture as the Pi) by `sh drive/build-drive.sh <drive>`. The Mac uses its own local `.venv` for development.
- Updating the app = `sh drive/update-drive.sh <drive>` from a clean checkout (replaces `app/` and the scripts; packages, debs and `.mediatagger/` are left alone). No install step.
- The menu entry depends on the drive mounting at the same path (`/media/<user>/MEDIATAGGER`), so the label must stay fixed.
- **The app's own drive is never written while the app runs.** No library is ever created on it (media stored there is viewing only), Python bytecode is precompiled when the drive is built and `PYTHONDONTWRITEBYTECODE=1` is set, and backups/thumbnails go to the Pi's home folder. Libraries live only on media drives.

### Spike results (2026-10-08)

`spikes/mpv_qt_embed.py` (libmpv render API in a `QOpenGLWidget`) on AVI/Xvid, MPEG-2, HEVC 1080p and GIF:

| Machine | Result |
|---|---|
| Mac (Apple GPU) | all formats play; HEVC hardware-decoded (`videotoolbox-copy`) |
| Pi 4 (V3D GPU, Wayland), run from the drive | all formats play, picture confirmed by eye; **HEVC hardware-decoded (`drm`)** |
| VM (UTM, `llvmpipe` software GL) | plays, but ~1 in 8 frames shows black or partly drawn |

**The VM is for logic, startup and packaging checks only, never for judging picture quality.** It has no GPU.

`setup-pi.sh` on the real Pi installed only `libmpv2` plus `libmujs3 libsixel1 libsndio7.0 libva-wayland2 libxpresent1`, offline, from the drive. The `_apt ... Permission denied` notices from apt are harmless (exFAT files aren't readable by apt's sandbox user, so it downloads as root).

Fallback: the Pi 4 has Wi-Fi, so a one-off phone hotspot can fetch packages if the drive's copies ever fall short.

## Deferred (not in this plan)

- Recursive slideshow (`r`), walked lazily.
- Automatic metadata (size, duration, resolution, date taken) bucketed into sensible groups, kept separate from user tags.
- Comparison search (`size>500MB`, `duration<30s`), depends on automatic metadata.
- Undo (`u`) for tag changes.
- Relinking orphaned tags after files move.
- Sort by date / sort toggle.
- 2×2 collage folder tiles.
- Warm the whole thumbnail cache in one go.
- Auto-advance slideshow.
- Multiple drives at once.
- Grid multi-select (folders cover bulk tagging).
