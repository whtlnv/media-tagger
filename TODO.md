# TODO

## Phase 25 — `1`–`9` jump through the video in ninths

- [ ] In the viewer on a 90 s video playing at 0:30, `1` jumps to 0:00
- [ ] In the viewer on a 90 s video playing at 0:30, `0` leaves it playing at about 0:30
  - predicted-contradiction: `src/mediatagger/test_video_controls.py::test_zero_on_a_playing_video_seeks_back_to_the_start` — asserts: `0` on a playing video seeks to 0:00 — retired-by: "`0` no longer jumps (Phase 26 gives it a new job)"
- [ ] In the viewer on a 90 s video, `2` jumps to 0:10 (one ninth in)
  - predicted-contradiction: `src/mediatagger/test_video_controls.py::test_a_key_on_a_playing_video_whose_progress_bar_is_hidden_shows_the_bar_at_once_reading_any_change[5 seeks to half its length and shows the bar]` — asserts: `5` on a 64 s video seeks to 0:32 (50 %) — retired-by: "`n` (1–9) jumps to (n − 1)/9 of the video"
- [ ] In the viewer on a 90 s video, `9` jumps to 1:20 (the start of the last ninth), not the end
- [ ] The cheat sheet lists `1–9` as jumping through the video in ninths and no longer lists `0` as a jump
- [ ] Running the shipped `mediatagger` command on a 90 s video and pressing `9` shows the progress bar at 1:20
- [ ] Acceptance: a screenshot of `mediatagger <folder>` on the Mac shows the cheat sheet's `1–9` ninths row
