# MediaTagger — Plan

Delivery phases, in order. Decisions, key maps and rules live in `DESIGN.md`; every phase follows it.
Each phase must end with its behavior reachable from the shipped `mediatagger` command, not only from tests.


Phases 1–11 are delivered (2026-10-14). Their specs are in git history (`PLAN.md` at `fcd5d3b`) and their items in `DONE.md`.

## Phase 12 — Fixes from the second Pi run

From the user's Pi test of build 3bd9a25 (findings and logs in `spikes/drive/pi-results-2026-10-14/`).

- **`o` opens another folder or drive from anywhere.** Today `o` only works on the empty launch screen; after launch reopened the last folder there was no way to open a different drive. `o` in the grid and in the viewer opens the folder picker; choosing a folder on another drive opens it (and that drive's library) as if the app had been started on it.
- **Dropping a folder from another drive opens it.** On the Pi, dragging a folder onto the app didn't open it. Reproduce first (grid and viewer, same drive and another drive); a drop opens the folder exactly like `o`.
- **Quitting after a long session returns the terminal promptly.** After a long session, Esc to quit left the terminal unresponsive. Find what keeps the process alive (suspects: thumbnail workers, the video player, the library backup) with a test that quits after a session with work still in flight, and make quitting finish within a couple of seconds.
- **No flood of Wayland text-input warnings.** `qt.qpa.wayland.textinput … Trying to disable … but 0x0 is focused` is printed many times per session; the app silences that logging category (only it).
- **The video progress bar is just the bar.** Drop the darker backdrop behind the progress bar; keep the light progress line and the `elapsed / total` text readable over black and white video.

## Phase 13 — Video speed, rotation and showing the controls

- **Playback speed.** `]` speeds up and `[` slows down, through 0.25×, 0.5×, 0.75×, 1×, 1.25×, 1.5×, 2×, 3×, 4×, 6×, 8× (stopping at the ends). The current speed shows with the progress bar whenever it isn't 1× (e.g. `1:23 / 4:56 · 2×`), and pressing a speed key shows the bar. Each new video starts at 1×.
- **Rotate.** `r` turns the shown video 90° clockwise (four presses come back round). Only while viewing it: the next item, or reopening it, starts unrotated.
- **Show the controls.** `v` only shows the video's progress bar (it hides again after 3 s like any key); it changes nothing else.
- The new keys only work while a video is shown; they never reach the grid or the tag prompt.

## Phase 14 — Zoom

- **Mouse-wheel zoom on images and videos.** Scrolling up zooms in, scrolling down zooms out, from 100 % (fitted, as today) to 300 %, in small steps. The point under the mouse stays under the mouse while zooming. Never below 100 %.
- Zoom resets to 100 % when moving to another item. Rotation (Phase 13) and zoom work together.

## Phase 15 — Key cheat sheet

- **`h` toggles a cheat sheet of every key and what it does**, drawn as the app's background instead of flat black (grid, viewer and launch screen), dim enough that tiles, images and videos stay on top and readable. It lists the keys of the screen you're on. `h` again hides it; whether it's shown is remembered in `state.json`.

## Phase 16 — Required tags

- **A drive can name the tag roots every file should have.** `mediatagger_config.json` at the drive's root (next to the media, where it's obvious which drive it configures) may hold `{"requiredRoots": ["type:", "size:"]}`. The app reads it when it opens the drive; the app never writes it.
- **Grid tiles mark files missing required tags.** A file is missing a root when none of its effective tags (own and inherited) starts with it. Its tile shows a small `✗` badge with the number of missing roots, styled like the tag-count badge; a file missing none shows nothing. With no config file, or no `requiredRoots`, no tile is marked.
- A config file that can't be read or isn't valid JSON doesn't stop the app: the status bar says so and no tile is marked.
- Tagging an item updates its mark at once.

## Phase 17 — Grid filters

- **A round floating button in the grid's bottom corner** (mouse only for now) opens a small menu of filters: **With tags**, **No tags**, **Missing tags** (only offered when the drive has required roots, Phase 16). Choosing one shows only the files that match; they're mutually exclusive; choosing the active one again turns filtering off. The button shows when a filter is on.
- Filters apply to the files of the folder shown; folder tiles stay so you can still move around. The filter lasts while the app runs and applies to every folder opened.
