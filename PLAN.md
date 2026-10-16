# MediaTagger — Plan

Delivery phases, in order. Decisions, key maps and rules live in `DESIGN.md`; every phase follows it.
Each phase must end with its behavior reachable from the shipped `mediatagger` command, not only from tests.


Phases 1–17 are delivered. Their specs are in git history (`PLAN.md` at `fcd5d3b` for 1–11, at `ca048de` for 12, at `76e644f` for 13, at `5ba4a0a` for 14, at `9a27389` for 15, at `213f913` for 16, at `f1a53c2` for 17) and their items in `DONE.md`.

## Phase 18 — Video chapters

Designed with the user (2026-10-14). A chapter is a tag at a moment: the video carries the tag as usual (overlay, badge count, search, autocomplete all unchanged) and the library also records the moments where it happens.

- **Adding.** While a video is shown, `c` opens the tag prompt (same look and autocomplete as `t`) and captures the playback time at the moment `c` is pressed. The video keeps playing while you type. Enter adds every word as a tag of the video with that moment; Esc cancels. A word the video already has as a tag just gains the moment. `-word` isn't accepted in this prompt (it only adds). A tag can have several moments; adding it again within 1 s of one of its moments adds no duplicate.
- **Seeing them.** Each moment is a small tick on the video's progress bar. Video tiles with moments show `⏱ 3` (symbol, space, number of distinct moments) in the top-right corner after the tag-count badge (left to right: missing — Phase 16 — tags, moments). The tag overlay and status bar are unchanged.
- **Jumping.** `.` jumps to the next moment and `,` to the previous one (no wrap-around); each jump shows the progress bar with the tag name (`goal · 1:23 / 4:56`). On a video with no moments they do nothing.
- **Chapter list.** `l` toggles an overlay listing the video's moments in time order, one line per moment with its tags (`1:23 goal, people:ana`), or "No chapters". `↑`/`↓` move the highlight (they don't seek while it's open), Enter jumps there and closes the list, Esc closes it, Backspace deletes the highlighted moment (no confirmation). The video keeps playing behind it.
- **Removing.** Deleting a moment keeps the tag on the video. Removing the tag with `t` (`-goal`) removes it and all its moments. No editing a moment's time or name: delete it and add it again.
- **Where it works.** `c`, `l`, `.`, `,` only while a video is shown; nothing on images; never in the grid or the tag prompt. Adding or deleting with no library or on a read-only drive behaves like `t` (the status bar says tags can't be saved); listing and jumping work wherever moments can be read. Moments are stored to 0.1 s and shown as `m:ss` (`h:mm:ss` from an hour), belong to the video file only (no inheritance; folders have none), and live in a new library table: existing libraries are upgraded on open like the schema-2 upgrade, and a read-only drive left at an older schema simply has no chapters.
- Search is unchanged: a result video opens at its start.
