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

- **What a thumbnail is.** Images: decoded with Qt at reduced size (`QImageReader.setScaledSize`, EXIF orientation applied) to fit the largest tile (~400 px). Videos: one frame at ~10% of the duration, taken with `ffmpeg`; the duration comes from `ffprobe`. Both run as subprocesses with a timeout. A missing `ffmpeg`/`ffprobe`, an unreadable or corrupt file, or a timeout leaves the tile's glyph in place and never crashes or stalls the grid; such a failure is cached like a success so it is not retried on every visit (until the file's size or mtime changes).
- **Folder tiles** show the thumbnail of the first image directly inside the folder (natural order, as listed by `folder.py`); a folder with no image keeps the folder glyph. Finding that image is background work, never done while painting.
- **Video tiles** show the duration (`m:ss`, or `h:mm:ss` from an hour) alongside the ▶ badge; the duration is cached with the thumbnail.
- **Order of work.** Opening a folder's grid requests thumbnails for the tiles in view first, most recent request first (scrolling or moving the cursor makes the newly visible tiles jump the queue), with 3 workers; when those are done, the rest of the folder is generated in the background. Leaving a folder drops its pending requests (work already running may finish and is cached). Workers never touch widgets; results reach the grid on the GUI thread, and only the affected tile repaints.
- **Cache.** `<cache home>/mediatagger/<drive_id>/thumbs.db`, where `<cache home>` is `$XDG_CACHE_HOME` if set, else `~/.cache`: one SQLite file holding thumbnails as compressed image blobs, keyed by the path relative to the drive root plus size and mtime. A cached entry whose file has the same size and mtime is used as is; a changed file is regenerated. With no library (viewing only, system disk, the app's own drive, declined) there is no drive id: thumbnails are generated and kept in memory for the session only, never written to disk. The cache is never written on the app's own drive or the drive being viewed. The conftest points `XDG_CACHE_HOME` at a per-test temp folder before the first test that writes the cache.
- **Status bar.** While thumbnails are being generated: `⟳ Generating thumbnails 132 / 1,204` (counting only what had to be generated in this folder, thousands separated); on completion `✓ Thumbnails ready`, cleared like other finished background messages. A folder whose thumbnails are all cached shows nothing. It shares the existing background-work slot with backups.
- **Tiles look.** The thumbnail fills the tile above the filename, keeping its aspect ratio; badges (tag count, ▶ and duration) sit over the thumbnail, legible on any picture. Phase 7's tiles read as sparse on the real screen (tiny glyphs, badges on the cell edges); this phase redoes the look and the orchestrator checks it on the native display.
- **Painting** still never stats, decodes or queries: the delegate draws from data already in the model.
- **Scale.** Opening the grid of a 5,000-file folder stays as responsive as in Phase 7 (the existing timing test keeps passing), and a second visit to a folder generates nothing.

## Phase 9 — Tag folders and inherited tags

`t` in the grid tags the selected item, including folders. A file's effective tags are its own plus those of every ancestor folder. The viewer's tag overlay shows inherited tags dimmed and own tags normal.

- **`t` in the grid** opens the same tag prompt as the viewer, for the item under the grid cursor — file or folder — with everything Phases 4–5 give it: it shows the item's own tags; `beach family` adds, `-sunset` removes; lowercased and trimmed; autocomplete (most used first, `people:` lists the namespace, `-` suggests the item's own tags); `Esc` closes the popup, then the prompt; failure keeps the text and shows `Couldn't save tags — is the drive still connected?`. While the prompt is open the grid ignores every key (no cursor moves, no `Enter`, no `Backspace`, no zoom, no quitting on `Esc`). It sits at the bottom centre above the status bar, never clipped, readable over thumbnails.
- **Where tags can't be saved** (no library, declined, can't be opened, read-only, system disk, the app's own drive) `t` in the grid briefly shows `Tags can't be saved here`, as in the viewer.
- **Folder tags** are stored like file tags, by the folder's path relative to the drive root, marked as a folder (the `items.kind` column, `'dir'`); the drive's mount point itself is never tagged. Tagging a folder never writes anything for the files inside it.
- **Effective tags** of an item = its own tags ∪ the own tags of every ancestor folder up to (not including) the drive root, computed when read, in one query per item. A tag that is both own and inherited counts as own. The library offers this to later phases (Phase 10 searches effective tags).
- **Viewer overlay** shows the current file's effective tags: own tags first in the normal style, then inherited tags dimmed (clearly lighter, still readable over black and bright images), each group alphabetical. A file with only inherited tags still shows the overlay. Tagging a folder in the grid and opening a file inside it shows the new inherited tags at once.
- **Grid:** a tile's `🏷N` badge still counts the item's own tags only (folders included); after saving in the grid the tile's badge and the status bar update at once, without re-listing the folder. Moving the cursor shows the selected item's own tags in the status bar, followed by its inherited tags dimmed.
- **Autocomplete counts** a folder as one item when ordering by use.
- **Scale:** opening a folder of 5,000 files and moving the cursor stay as responsive as in Phase 8 (the timing tests keep passing); showing a file's effective tags is one query.

## Phase 9a — Fixes from the first Pi run, and video controls

From the user's Pi test of build ff64cc3 (logs in the stick's `results/`, findings 2026-10-11).

- **Esc back to the grid always works.** Opening a file from the grid stops its thumbnails; Esc then stopped them a second time and raised `Internal C++ object (_Generated) already deleted` once Qt had deleted the object in between, so the grid never came back. Stopping a folder's thumbnails is safe any number of times, at any point after Qt has processed deferred deletions; a regression test flushes deferred deletes between opening a file and pressing Esc.
- **A relative path at launch** (`mediatagger media/clip.mp4`) opens like the absolute path, instead of crashing with `StopIteration` looking for its drive.
- **Seeking never raises.** If mpv refuses a seek (it did on the Pi: `Error running mpv command -12`), the key does nothing visible and the app carries on; no exception escapes a key handler.
- **Video playback never leaks file descriptors** (delivered separately once the Pi diagnostic is back — not part of this phase's TODO). On the Pi (Mesa v3d, Wayland) the app gained one open file per frame until `Too many open files` killed the Wayland connection after ~30 s; the Linux VM (llvmpipe) holds steady at 42. The fix depends on `diag-video.sh` results from the Pi (which mpv/Qt setting leaks). Whatever it is, a test plays a clip for a while and asserts the process's open-file count stays flat (Linux/macOS: count /proc/self/fd or `os.listdir('/dev/fd')`).
- **Entering a folder refreshes the status bar.** Opening a folder's grid (Enter on a folder, Backspace, Esc from the viewer, launch) shows the tags of the item under its cursor at once; today the status bar keeps the previous selection's tags until the cursor moves (found validating Phase 9: entering a tagged folder showed the folder's own tags in white as if they were the first file's).
- **`t` in an empty folder** does nothing (today it raises `AttributeError: 'NoneType' object has no attribute 'path'` in `Window._tag`).
- **Status bar shows only problems.** No `Library: <drive>` label when a library is open and writable; still `No library open` / viewing only, `Library on <drive> can't be opened — viewing only`, `Read-only — tags can't be saved`, background work (thumbnails, backups), and the selected item's tags.
- **Video progress.** While a video plays, a thin progress bar with `elapsed / total` (`1:23 / 4:56`, hours from an hour) runs along the bottom of the video, above the status bar. It appears when a video starts, on any seek and on any key, and fades after ~3 s of no input. It is readable over black and bright frames and never covers the tag prompt.
- **Seeking.** ↑/↓ keep seeking ±10 s; `0`–`9` jump to 0 %–90 % of the video. Each seek shows the progress bar. The keys are only active while a video is shown; they never reach the grid or the tag prompt.
- **Windowed by default.** The app opens as a normal, resizable window (about 80 % of the screen, centred; remembered size and position in `state.json` when known), not fullscreen. `f` toggles fullscreen in both grid and viewer, as before.

## Phase 9b — Video playback never leaks

The Pi crash from the first Pi run: libmpv 0.40/0.41's render API creates a GL fence after every rendered frame and never deletes it (mpv#17217, fixed upstream in f74adc4 but in no release or Debian package yet; the Pi has `libmpv2 0.40.0-3+deb13u1`). On the Pi's Mesa v3d each fence holds a `sync_file` fd, so after ~30 s the app runs out of file descriptors and the Wayland connection dies. Write-up: `spikes/mpv-fence-leak/REPORT.md`.

- **The video surface hands mpv a `glFenceSync` that creates no fence.** When mpv asks the surface's OpenGL context for `glFenceSync`, it gets a stand-in that returns no fence (null); mpv then keeps nothing to leak. Every other GL function resolves to the context's real one, as today. The stand-in stays alive as long as the surface's render context. `glFenceSync` must still resolve to something: it is core in GLES 3 (the Pi) and mpv refuses to start if a core function is missing.
- **The viewer's player runs without direct rendering** (`vd-lavc-dr=no`): mpv's only other fence use is for directly-rendered buffers, which would otherwise be treated as reusable at once.
- **Playback is otherwise unchanged:** clips still play, seek and show their progress; a player created with extra options (tests' `ao=null`) still gets `vd-lavc-dr=no`.
- **Native checks (orchestrator):** on the Mac, live GL fences in the real app stay flat while a clip plays (wrapping as in `spikes/fence_check_mac.py`); on the Pi, the app's `sync_file` fd count stays flat and a video plays for several minutes.

## Phase 10 — Search

`/` focuses a search bar above the grid. Queries support AND (`beach family`), NOT (`-sunset`), OR (`beach|pool`), exact tags and namespace prefixes (`people:`), matched against effective tags. Results show only tagged items, collapsed so that a matching folder hides any matching items inside it. `Enter` on a result file starts a slideshow over the results from that file; `Enter` on a result folder opens that folder normally. A breadcrumb shows the active query; `Esc` clears it and returns to the folder you were in. Tagged paths that no longer exist appear as "missing" tiles whose tags can be removed. `↑` in the search bar recalls previous searches.

## Phase 11 — Run from the drive on the Pi

The Pi has no internet; the app runs from the USB drive (see DESIGN.md "Install: runs from the USB drive"). A script run in the arm64 trixie VM lays the app out on the drive: source, third-party Python packages for linux-aarch64/cp313, and the libmpv2 `.deb`s the Pi lacks. On a Pi with no network, a one-time `setup-pi.sh` from the drive installs libmpv2 and adds a "MediaTagger" desktop menu entry; from then on the app starts from the menu or with `sh run.sh` on the drive. Copying a newer `app/` onto the drive updates the app with no further setup, and the drive's tags are kept.
