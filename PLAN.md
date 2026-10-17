# MediaTagger — Plan

Delivery phases, in order. Decisions, key maps and rules live in `DESIGN.md`; every phase follows it.
Each phase must end with its behavior reachable from the shipped `mediatagger` command, not only from tests.


Phases 1–23 are delivered. Their specs are in git history (`PLAN.md` at `fcd5d3b` for 1–11, at `ca048de` for 12, at `76e644f` for 13, at `5ba4a0a` for 14, at `9a27389` for 15, at `213f913` for 16, at `f1a53c2` for 17, at `4cc0f4e` for 18, at `a2d1a4e` for 19, at `65d51a2` for 20, at `37d3379` for 21, at `37d3379` for 22, at `37d3379` for 23) and their items in `DONE.md`.

## Phase 24 — Viewer tags one per line

From the user's Pi notes of 2026-10-17 (`results/findings.txt`): "please make the tags in the viewer stack vertically, not horizontally".

- The viewer's tag overlay (top-right) shows one tag per line, right-aligned in the corner: the file's own tags first, then its inherited tags (still dimmed) below them. Same font, colours and corner. Many tags just make a longer column; nothing is cut. The grid's status-bar tags are unchanged.

## Phase 25 — `1`–`9` jump through the video in ninths

From the same notes: "0 is at the end of the line in the keyboard yet it takes me to the beginning. Let's try jumping through the video using 1-9 where 1 is 0:00 and each number advances the video (100/9)% until 9 that loads not the end of the video, but the last segment".

- In the viewer on a video, `n` (1–9) jumps to (n − 1)/9 of the video: `1` = 0:00, `2` = 11.1 %, … `9` = 88.9 % (the start of the last ninth). `0` no longer jumps (Phase 26 gives it a new job). DESIGN.md and the cheat sheet updated.

## Phase 26 — `0` puts the view back to normal

From the same notes: "now that 0 is free, let's have it restore zoom, rotation and playback speed to their default".

- In the viewer, `0` resets zoom to 100 % (centred), the turn to unturned and, on a video, the speed to 1×, all at once — exactly as the item first opened. Playback position and pause state are kept. On an image it resets zoom and turn. DESIGN.md and the cheat sheet updated; typed into a prompt it types `0`.

## Phase 27 — Badge symbols that show on the Pi

From the same notes: "the symbols you chose for tags and chapters appear as squares in the grid view".

- The tile badges' tag symbol (`🏷`, `grid.TAG_BADGE`) and chapter symbol (`⏱`, `MOMENTS_BADGE`) are emoji the Pi's fonts don't have. Draw both as small painted icons (QPainter shapes: a tag, a stopwatch or clock) at the size and colour the glyphs had, so they never depend on a font. Badge layout, numbers and `✕` are unchanged.
- Check the rest of the UI (cheat sheet, status bar, filter menu, chapter list, prompts) for any other character outside what the Pi's default fonts (DejaVu) cover, and fix any you find the same way or with a plain character.

## Phase 28 — Play a video backwards

From the same notes: "can we play the videos backwards??"

- In the viewer on a video, `b` toggles playing backwards (mpv `play-direction=backward`); `b` again plays forwards. Speed keys, pause, seeking, `u`/`e` frame steps and chapters keep working in either direction; the progress bar follows. Backwards playback loops like forwards (reaching 0:00 goes on from the end). Every video opens playing forwards; `0` (Phase 26) also sets forwards. DESIGN.md and the cheat sheet updated.
- mpv's backward playback decodes in chunks and can be heavy; find mpv settings that make it work on the Mac, keep the video leak rules (Phase 9b), and note in HANDOVER what the Pi should check (smoothness, memory, hwdec HEVC).
