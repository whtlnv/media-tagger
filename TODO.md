# TODO

## Phase 21 — Zoom to 500 %

- [x] Scrolling the mouse wheel up many notches over an image stops at five times its fitted size
- [x] Scrolling the mouse wheel up many notches over a playing video stops at five times its fitted size
  - predicted-contradiction: `src/mediatagger/test_viewer_zoom.py::test_scrolling_the_mouse_wheel_up_many_notches_over_a_video_stops_at_three_times_its_fitted_size` — asserts: 30 wheel notches up over a video leave mpv's video-zoom at log2(3), capped at 300 % — retired-by: "stops at five times its fitted size"
- [ ] A photo larger than five times the window, zoomed in to 500 %, shows its own fine detail rather than an enlarged copy decoded for a lower zoom
- [ ] A photo smaller than five times the window, zoomed in, is decoded no larger than its own pixel size
- [ ] In the shipped `mediatagger` app on a drive, scrolling the wheel up many notches over a photo shows it at 500 % of its fitted size
