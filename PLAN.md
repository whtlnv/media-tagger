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

## Phase 6 — Database backups

On start and on exit the library database is copied to `~/.local/share/mediatagger/backups/<drive_id>/`, keeping the 10 most recent. The status bar shows the backup running and finishing. If the drive's database is missing or corrupt, the app offers to restore from the latest backup.

## Phase 7 — Folder grid

`Esc` in the viewer opens a grid of the current folder: subfolders first, then media, natural order, with the cursor on the file that was being viewed. Arrows move, `Enter` on a file starts the slideshow there, `Enter` on a folder enters it, `Backspace` goes up (not above the library root). Tiles show a thumbnail, the truncated filename, and a tag-count badge for items with their own tags; video tiles show a ▶ badge and duration; folder tiles show their first image. `+`/`-` change tile size. The selected item's tags appear in the status bar. Launching with the last-used drive mounted reopens the last folder in the grid.

## Phase 8 — Thumbnails

Thumbnails are generated on demand for visible tiles, newest request first, then prefetched for the rest of the folder in the background. They are cached on the Pi per drive and regenerated only when the source file's size or mtime changes; a second visit to a folder generates nothing. The status bar shows progress (`⟳ Generating thumbnails 132 / 1,204`) and completion (`✓ Thumbnails ready`).

## Phase 9 — Tag folders and inherited tags

`t` in the grid tags the selected item, including folders. A file's effective tags are its own plus those of every ancestor folder. The viewer's tag overlay shows inherited tags dimmed and own tags normal.

## Phase 10 — Search

`/` focuses a search bar above the grid. Queries support AND (`beach family`), NOT (`-sunset`), OR (`beach|pool`), exact tags and namespace prefixes (`people:`), matched against effective tags. Results show only tagged items, collapsed so that a matching folder hides any matching items inside it. `Enter` on a result file starts a slideshow over the results from that file; `Enter` on a result folder opens that folder normally. A breadcrumb shows the active query; `Esc` clears it and returns to the folder you were in. Tagged paths that no longer exist appear as "missing" tiles whose tags can be removed. `↑` in the search bar recalls previous searches.

## Phase 11 — Run from the drive on the Pi

The Pi has no internet; the app runs from the USB drive (see DESIGN.md "Install: runs from the USB drive"). A script run in the arm64 trixie VM lays the app out on the drive: source, third-party Python packages for linux-aarch64/cp313, and the libmpv2 `.deb`s the Pi lacks. On a Pi with no network, a one-time `setup-pi.sh` from the drive installs libmpv2 and adds a "MediaTagger" desktop menu entry; from then on the app starts from the menu or with `sh run.sh` on the drive. Copying a newer `app/` onto the drive updates the app with no further setup, and the drive's tags are kept.
