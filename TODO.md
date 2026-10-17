# TODO

## Phase 26 — `0` puts the view back to normal

- [x] In the viewer on a photo zoomed in with the mouse wheel, `0` shows it back at 100 %, centred, as it first opened
- [x] In the viewer on a photo turned once with `r`, `0` shows it unturned
- [x] In the viewer on a photo turned with `r` and then zoomed in, `0` shows it unturned at 100 %, centred, in one press
- [x] In the viewer on a video playing at 2×, `0` sets its speed back to 1×
- [x] In the viewer on a video zoomed in with the mouse wheel, `0` shows it back at 100 %, centred
- [x] In the viewer on a video turned once with `r`, `0` shows it unturned
- [x] In the viewer on a video paused at about 0:30, `0` leaves it paused at about 0:30
- [x] In the viewer with the tag prompt open on a zoomed photo, `0` types `0` into the prompt and leaves the zoom as it was
- [x] The cheat sheet and DESIGN.md's viewer key table list `0` as putting zoom, turn and speed back to normal
  - predicted-contradiction: `src/mediatagger/test_cheat_sheet.py::test_the_viewer_cheat_sheet_and_designs_viewer_table_both_list_1_to_9_as_jumping_in_ninths_and_no_key_for_0` — asserts: neither the viewer cheat sheet nor DESIGN.md's viewer table has any key containing `0` — retired-by: "The cheat sheet and DESIGN.md's viewer key table list `0` as putting zoom, turn and speed back to normal"
- [ ] Running the shipped `mediatagger` command on a video, pressing `]` then `0`, leaves it playing at 1×
