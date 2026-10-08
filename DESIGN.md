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
- First time on a drive: ask "Create a tag library on <drive>?" before writing anything.
- Read-only drive: browsing and viewing work; tagging is disabled, with a banner saying so.
- Each library has a unique `drive_id` stored in its DB. One drive at a time.
- **Only tagged items are stored.** Untagged directories are never indexed. Browsing reads the filesystem live.
- A tagged path that no longer exists shows as a **missing** tile in results; its tags can be removed from there. No rename/move tracking.

### Backups

On app start and exit, copy `tags.db` with the SQLite backup API to `~/.local/share/mediatagger/backups/<drive_id>/`, keeping the last 10. If the drive's DB is missing or corrupt, offer to restore the latest backup.

### Thumbnail cache

On the Pi, not the drive: `~/.cache/mediatagger/<drive_id>/thumbs.db` (thumbnails as blobs in one SQLite file). Keyed by relative path + size + mtime, so each is generated once and regenerated only when the file changes.

## Tags

- Lowercased, trimmed. Hyphens join words (`day-at-beach`; typed spaces inside one tag are not possible because space separates tags).
- Colons namespace tags, any depth: `people:ana`, `place:mexico:cancun`. Stored whole, as plain strings.
- Tags can be on **files** or **directories**.
- **Inheritance:** an item's effective tags = its own tags ∪ the tags of every ancestor directory.

### Tag prompt (`t`)

- Shows the item's current own tags.
- `beach family` adds both; `-sunset` removes `sunset`.
- Autocomplete over existing tags, most used first; typing `people:` lists all `people:*` tags.

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

Search history is remembered (`↑` in the search box).

## Media

- Images: jpg, jpeg, png, webp, bmp, tif, tiff, heic.
- Video (played by mpv): mp4, mov, avi, mpg, mpeg, mkv, m4v, wmv, 3gp, **gif**.
- Order: natural filename sort (`IMG_2` before `IMG_10`), folders first in the grid.
- Slideshow covers the current folder only (non-recursive).

## Screens and keys

### Launch

- If the drive from last session is mounted: reopen the last folder in the grid.
- Otherwise: empty screen "Drop a folder or file here, or press `o` to open".

### Drag & drop

- Drop a folder: start the slideshow of that folder.
- Drop a file: slideshow of its folder, starting at that file.

### Viewer (fullscreen)

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
| `m` | mute |

- Images fit to screen.
- Video autoplays **with sound**, loops. Space never pauses.
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
| `Esc` | (in search) clear search, back to the folder |

- Tiles ~200 px: thumbnail, truncated filename, tag-count badge when the item has own tags.
- Video tiles: frame at ~10%, ▶ badge, duration.
- Folder tiles: first image inside.
- Selected item's full tags shown in the status bar.

### Status bar (always visible)

Any background work is announced and its completion shown, e.g. `⟳ Generating thumbnails 132 / 1,204` → `✓ Thumbnails ready`, `⟳ Backing up database…` → `✓ Backed up`. Nothing runs silently.

Thumbnail generation: on demand for visible tiles (3 workers, newest request first), then background prefetch of the rest of the current folder.

## Install

The Pi has **no internet** (Bluetooth only). Install and updates are fully offline, carried on the USB drive:

- An **offline bundle** is built in the arm64 trixie VM: the app source, a `uv` arm64 binary, Python wheels for aarch64/cp313 (PySide6, python-mpv, Pillow…), and `.deb`s for any system packages (libmpv, ffmpeg) the Pi doesn't already have, dependencies included.
- The bundle is copied to the drive (e.g. `<root>/.mediatagger/dist/`).
- `install.sh` on the Pi installs the `.deb`s, creates the environment from the local wheels only (`uv --offline`), and adds a "MediaTagger" `.desktop` menu entry.
- Updating = rebuild bundle, copy to drive, re-run `install.sh`.
- Uses the Pi's system Python 3.13 (trixie default), so no Python download.

Fallback if the bundle ever gets stuck: the Pi 4 has Wi-Fi, so a one-off phone hotspot can do an online install.

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
