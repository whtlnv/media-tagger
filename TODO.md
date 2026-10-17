# TODO

## Phase 23 — `r` turns images too

- [x] Pressing `r` on a landscape image in a square viewer shows it turned 90° clockwise (its top-left corner now drawn at the top-right) and drawn whole across the viewer's full height
- [x] Pressing `r` twice on an image shows it upside down (its top-left corner drawn at the bottom-right)
- [x] Pressing `r` four times on an image shows it unrotated again, drawn exactly where it was fitted before the first press
- [x] A landscape image turned once in a wide viewer is fitted whole: its turned height fills the viewer's height and it is centred across the width
- [x] After pressing `r` on an image, moving to the next image shows that image unrotated
- [x] After pressing `r` on an image, moving to the next item and back shows the first image unrotated again
- [x] After pressing `r` on a video, moving to the next item shows an image there unrotated
- [x] Pressing `r` on an image leaves the image file's bytes and modification time unchanged
- [x] After pressing `r` on an image and `Esc` to the grid, that image's tile shows the same thumbnail as before the press
- [x] Typing `r` in the tag prompt open over an image types `r` and leaves the image unturned
- [ ] Pressing `r` on an image zoomed in one notch shows it turned and still at 110 % of its turned fitted size
- [ ] Zooming in on a turned image with the mouse off its centre keeps the picture point under the mouse under the mouse
- [ ] Zooming a turned image back out to fitted after zooming in with the mouse off its centre shows it exactly where it was fitted, centred
- [ ] Zooming out of a turned image that covers the window with the mouse near a window edge never leaves black between that edge and the image
- [ ] Pressing `r` on a zoomed-in image panned to a window edge leaves no black between that edge and the turned image (backlog: src/mediatagger/zoom.py:37 A zoom's pan is clamped only when the wheel turns, not when the window resizes or `r` turns a video)
- [ ] Pressing `r` on a zoomed-in image whose turned picture still covers the window where it lies keeps it at the same pan (backlog: src/mediatagger/zoom.py:37 A zoom's pan is clamped only when the wheel turns, not when the window resizes or `r` turns a video)
- [ ] A landscape photo larger than the viewer, turned once, is drawn sharp at the viewer's full height: decoded to fit the turned picture, not the unturned one
- [ ] Pressing `r` on an image shown after a paused video turns the image and leaves the idle player's rotation unchanged
- [ ] In the window opened on a folder of a landscape image, pressing `r` in the viewer shows the image turned 90° clockwise, fitted whole
