# MediaTagger — Plan

Delivery phases, in order. Decisions, key maps and rules live in `DESIGN.md`; every phase follows it.
Each phase must end with its behavior reachable from the shipped `mediatagger` command, not only from tests.


Phases 1–18 are delivered. Their specs are in git history (`PLAN.md` at `fcd5d3b` for 1–11, at `ca048de` for 12, at `76e644f` for 13, at `5ba4a0a` for 14, at `9a27389` for 15, at `213f913` for 16, at `f1a53c2` for 17, at `4cc0f4e` for 18) and their items in `DONE.md`.

## Phase 19 — Rename a tag across the library

Designed with the user (2026-10-16).

- **`n` in the grid** (folder grids and search results) opens a one-line prompt in the tag prompt's style, labelled `Rename tag:`. You type the old tag, a space and the new tag (`beach places:beach`); tags never contain spaces. Autocomplete offers existing tags for both words. `Enter` applies, `Esc` cancels, `↑`/`↓` recall earlier renames (remembered in `state.json` like searches). `n` never works in the viewer, and typed into the tag prompt or search bar it types an `n`.
- **The rename applies to the whole library of the drive**, files and folders alike: every item tagged with exactly the old tag has it replaced by the new one. An item that already has the new tag keeps it once (so renaming into an existing tag merges the two). Chapter moments of the old tag become moments of the new one; two moments of the tags within 1 s of each other become one.
- **Safety:** right before applying, the library is backed up with the existing backup system (Phase 6), so a bad rename can be undone by restoring that backup. No confirmation step: `Enter` applies at once, in one transaction.
- **Feedback:** the status bar says `Renamed beach → places:beach on 42 items`. No item tagged with the old one: `No tag "beach"`, nothing changes. Names are lowercased like `t`. Anything other than exactly two words, renaming a tag to itself, or a name starting with `-`: a short status message, nothing changes. No library or a read-only drive: the same "tags can't be saved" message as `t`.
- **Everything shown updates at once:** tag-count, `✕` and `⏱` badges, the status bar's tags, the open grid and search results (and filters re-apply).
- `n` is added to the grid's key table in DESIGN.md and to the cheat sheet.
