# MediaTagger — Plan

Delivery phases, in order. Decisions, key maps and rules live in `DESIGN.md`; every phase follows it.
Each phase must end with its behavior reachable from the shipped `mediatagger` command, not only from tests.

## Phase 1 — Open a folder and step through it

Running `mediatagger <path>` opens a fullscreen viewer. A folder path shows its images and videos one at a time in natural filename order, starting at the first; a file path shows its folder starting at that file. Non-media files are skipped. `Space`/`→` go to the next item and `←` to the previous; navigation stops at the ends. Images fit the screen. Videos (including GIFs and AVI/MPG) autoplay with sound and loop; `p`/`Enter` toggles pause, `↑`/`↓` seek ±10 s, `m` mutes. `i` toggles an overlay with the filename and position (`3 / 120`). `f` toggles fullscreen. Files that can't be decoded show an "unsupported" placeholder instead of crashing.

## Phase 2 — Drag and drop, and the launch screen

Launching with no path shows an empty window saying "Drop a folder or file here, or press `o` to open". `o` opens a folder picker. Dropping a folder onto the window starts its slideshow; dropping a file starts its folder's slideshow at that file. Dropping a new folder while viewing replaces the current slideshow.

## Phase 3 — Library on the drive

Opening anything on a drive locates the drive's mount point as the library root. If the root has no `.mediatagger/tags.db`, the app asks before creating it; declining still allows viewing. A read-only drive shows a banner that tags can't be saved, and viewing still works. Each library gets a stable drive id. The status bar exists and reports library state.

## Phase 4 — Tag the current file

In the viewer, `t` opens a prompt showing the file's current tags. Entering `beach family` adds both; `-sunset` removes `sunset`. Tags are lowercased and trimmed; colon-namespaced tags of any depth (`place:mexico:cancun`) are stored whole. Tags persist on the drive with paths relative to the root, so they survive restarting the app and remounting the drive at a different path. A corner overlay shows the current file's tags. `Esc` cancels the prompt. Tagging is disabled on a read-only drive.

## Phase 5 — Autocomplete

The tag prompt suggests existing tags as you type, most used first. Typing a namespace prefix (`people:`) lists every tag under it.

- Suggestions come from the current drive's library, ordered by how many items carry the tag (ties alphabetical).
- Completion works on the word being typed — the last space-separated token. In `beach fam` it completes `fam` → `family` and keeps `beach `; accepting replaces only that token.
- A namespace prefix (`people:`) lists every tag under it, at any depth (`people:ana`, `people:luis`, …).
- A token starting with `-` (removal) suggests from the current item's own tags and keeps the `-`.
- Matching is case-insensitive. Tokens already entered, and tags the item already has (for additions), are not suggested again.
- `↓`/`↑` move through the suggestions; `Tab` or `Enter` accepts the highlighted one. `Enter` with no popup saves as before.
- The first `Esc` closes the popup; `Esc` with no popup cancels the prompt as before. `Esc` never quits the app while the prompt is open. While the prompt is open the slideshow and video ignore every key, including the arrows the popup uses.
- The popup matches the overlays' style, is readable over black and bright images, and is never clipped off-screen (it opens upward from the prompt near the bottom).
- On a drive with no tags yet, no popup appears.
- Typing stays responsive with thousands of tags: one SQL query per keystroke, or a cache per prompt-open invalidated on save.
- If saving fails because the drive has gone away (`sqlite3.Error` or `OSError` from the library), the prompt stays open with its text and the status bar says "Couldn't save tags — is the drive still connected?".

## Phase 6 — Database backups

On start and on exit the library database is copied to `~/.local/share/mediatagger/backups/<drive_id>/`, keeping the 10 most recent. The status bar shows the backup running and finishing. If the drive's database is missing or corrupt, the app offers to restore from the latest backup.

- Backups go to `<data home>/mediatagger/backups/<drive_id>/`, where `<data home>` is `$XDG_DATA_HOME` if set, else `~/.local/share` (same on macOS). The backup folder is injectable (`backup_root=`) so tests never touch the real home folder.
- Each backup is made with SQLite's online backup API (never a file copy), named sortably by UTC time (`tags-20261009T153000Z.db`, from an injectable clock). Only the 10 newest are kept; older ones are deleted.
- Next to the backups, `drive.json` records the drive's name (its mount point's folder name) and drive id, so a drive whose `tags.db` is missing or unreadable can be matched to its backups by name.
- A backup is made when a drive's library has opened successfully, and when the viewer closes or switches to another path. Never for a library that failed to open, never when nothing changed since that drive's last backup (compare a content hash of the database), and never on the app's own drive or the system disk (they have no library).
- The status bar shows `⟳ Backing up database…` while it runs, then `✓ Backed up` (cleared after a few seconds), or `✗ Backup failed: <short reason>` (e.g. the home folder isn't writable). A failed backup never crashes the app or blocks viewing or tagging. The exit backup finishes before the app exits. This background-work message is reusable by later phases.
- When `tags.db` is garbage or gone while `.mediatagger/` exists and backups exist for a drive of the same name, the app asks "The tag library on <DRIVE> is missing or damaged. Restore the backup from <date time>?" (injectable, like `ask_to_create_library=`). Yes: the damaged file is kept as `.mediatagger/tags.db.damaged-<timestamp>`, the newest backup is restored with the backup API, the library opens normally and the status bar shows `✓ Restored backup from <date time>`. No: the existing behaviour (`Library on <DRIVE> can't be opened — viewing only`, or the create question if `tags.db` is missing).
- A read-only drive can't be restored to: the status bar says so and the drive stays viewing only. Restoring never writes to the app's own drive.

## Phase 7 — Folder grid

`Esc` in the viewer opens a grid of the current folder: subfolders first, then media, natural order, with the cursor on the file that was being viewed. Arrows move, `Enter` on a file starts the slideshow there, `Enter` on a folder enters it, `Backspace` goes up (not above the drive's mount point). Tiles show a type glyph where the thumbnail will go (Phase 8), the truncated filename, and a tag-count badge for items with their own tags; video tiles show a ▶ badge. `+`/`-` change tile size. The selected item's own tags appear in the status bar. Launching with no path reopens the last folder in the grid if it still exists.

- **Listing.** A folder is listed once when the grid opens it: its subfolders first, then its images and videos, each group in the existing natural, case-blind order (`folder.py`). Hidden folders (leading `.`), `.mediatagger` and macOS litter folders (`.Spotlight-V100`, `.fseventsd`, `.Trashes`) are never listed. Nothing is stat'ed or decoded while painting.
- **Tiles.** Each tile shows a lightweight placeholder where the thumbnail will go: a type glyph drawn by the tile painter (image, ▶ video, folder), the filename truncated with an ellipsis to the tile width, and a `🏷N` badge when the item has N > 0 tags of its own (no badge for untagged items). Video tiles show a ▶ badge. Video duration, real thumbnails and folder first-image previews are Phase 8: the tile's data and painter must leave a slot for a thumbnail so Phase 8 drops it in without restructuring.
- **Tag counts** for a folder's items come from one SQL query per folder opened, never one per tile. With no library (viewing only), no badges.
- **Keys in the grid:** arrows move the cursor; `Enter` on a file starts the slideshow of that folder at that file; `Enter` on a folder opens its grid with the cursor on its first entry; `Backspace` opens the parent folder's grid with the cursor on the folder just left, but never goes above the drive's mount point (for the system disk, `/`); `+`/`-` grow and shrink the tiles within sensible bounds (about 100–400 px, starting at ~200); `f` toggles fullscreen; `Esc` quits the app.
- **Keys in the viewer:** `Esc` goes back to the grid of the current item's folder with the cursor on that item. This replaces the interim "`Esc` quits"; an open tag prompt still takes the first `Esc` as before. On the launch screen (nothing open) `Esc` still quits.
- **Opening paths keeps its behaviour:** the launch screen, `o`, drag and drop and the command-line path still start the slideshow. Dropping a folder or file onto the grid starts its slideshow like a drop onto the viewer.
- **One window.** The shipped `mediatagger` command shows one top-level window that switches between the grid and the viewer. The status bar (library status, read-only notice, background-work slot) and the open library are shared by both: the library status and background messages stay visible in the grid, and moving between grid and viewer on the same drive does not re-open the library or back it up again.
- **Status bar:** moving the grid cursor shows the selected item's own tags (space-separated) in the status bar; an untagged item shows none.
- **Launch memory.** Whenever a folder's grid or slideshow is shown, the folder and its drive's mount point are recorded in `<config home>/mediatagger/state.json`, where `<config home>` is `$XDG_CONFIG_HOME` if set, else `~/.config`; the config home is injectable so tests never touch the real home folder (the conftest points `XDG_CONFIG_HOME` at a per-test temp folder, as it does for `XDG_DATA_HOME`). The state file is never written when it would land on the app's own drive or on the drive being viewed. Launched with no path: if the remembered folder still exists, its grid opens (with its drive's library opened as usual); otherwise, or with no or unreadable state, the launch screen shows.
- **Scale.** Folders can hold thousands of items on a USB stick on a Pi: opening the grid of a folder of 5,000 files stays responsive (pinned by a timing test like the 5,000-tag one), and repainting never stats or decodes files.

## Phase 8 — Thumbnails

Thumbnails are generated on demand for visible tiles, newest request first, then prefetched for the rest of the folder in the background. They are cached on the Pi per drive and regenerated only when the source file's size or mtime changes; a second visit to a folder generates nothing. The status bar shows progress (`⟳ Generating thumbnails 132 / 1,204`) and completion (`✓ Thumbnails ready`). Video tiles also show their duration, and folder tiles show their first image.

## Phase 9 — Tag folders and inherited tags

`t` in the grid tags the selected item, including folders. A file's effective tags are its own plus those of every ancestor folder. The viewer's tag overlay shows inherited tags dimmed and own tags normal.

## Phase 10 — Search

`/` focuses a search bar above the grid. Queries support AND (`beach family`), NOT (`-sunset`), OR (`beach|pool`), exact tags and namespace prefixes (`people:`), matched against effective tags. Results show only tagged items, collapsed so that a matching folder hides any matching items inside it. `Enter` on a result file starts a slideshow over the results from that file; `Enter` on a result folder opens that folder normally. A breadcrumb shows the active query; `Esc` clears it and returns to the folder you were in. Tagged paths that no longer exist appear as "missing" tiles whose tags can be removed. `↑` in the search bar recalls previous searches.

## Phase 11 — Run from the drive on the Pi

The Pi has no internet; the app runs from the USB drive (see DESIGN.md "Install: runs from the USB drive"). A script run in the arm64 trixie VM lays the app out on the drive: source, third-party Python packages for linux-aarch64/cp313, and the libmpv2 `.deb`s the Pi lacks. On a Pi with no network, a one-time `setup-pi.sh` from the drive installs libmpv2 and adds a "MediaTagger" desktop menu entry; from then on the app starts from the menu or with `sh run.sh` on the drive. Copying a newer `app/` onto the drive updates the app with no further setup, and the drive's tags are kept.
