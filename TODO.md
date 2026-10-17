# TODO

## Phase 22 — Frame step on a paused video

- [x] Pressing `u` on a paused video shows its next frame (its position moves forward by one frame and it stays paused)
- [x] Pressing `u` on a playing video does not step a frame (it keeps playing, its position not jumped)
- [x] Pressing `e` on a paused video shows its previous frame (its position moves back by one frame and it stays paused)
- [x] Pressing `e` on a playing video does not step a frame (it keeps playing, its position not jumped)
- [x] After `u` on a paused video, the progress bar shows and reads the stepped position
- [x] After `e` on a paused video, the progress bar shows and reads the stepped position
- [x] With the tag prompt open over a paused video, typing `u` and `e` puts those letters in the prompt and leaves the video's frame unchanged
- [x] With the chapter (`c`) prompt open over a paused video, typing `u` and `e` puts those letters in the prompt and leaves the video's frame unchanged
- [x] Pressing `u` or `e` on an image changes nothing (no error, the image stays shown)
- [ ] The `h` cheat sheet lists `u` (next frame) and `e` (previous frame) among the viewer's keys, matching new rows in DESIGN.md's viewer key table (the pinned test compares the two, so both change together)
- [ ] In the shipped `mediatagger` app on a drive, `u` on a paused video steps it one frame forward
