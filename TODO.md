# TODO

- [ ] Opening the app with no path shows an empty window with the text "Drop a folder or file here, or press `o` to open"
- [ ] Opening the app with a path shows that path's first item, not the "Drop a folder or file here" text
- [ ] Pressing `o` on the launch screen opens a folder picker
- [ ] A key other than `o` (e.g. `x`) on the launch screen opens no folder picker and leaves the launch text showing
- [ ] Choosing a folder in the `o` picker starts that folder's slideshow at its first item
- [ ] Cancelling the `o` picker leaves the launch screen showing its "Drop a folder or file here" text
- [ ] Dragging a folder or file from the file manager over the window is accepted as a drop
- [ ] Dragging something that is not a local file or folder (e.g. plain text) over the window is refused
- [ ] Dropping a folder onto the launch screen starts that folder's slideshow at its first item
- [ ] Dropping a file onto the launch screen starts its folder's slideshow at that file
- [ ] Dropping a folder while viewing another folder replaces the slideshow with the dropped folder's, starting at its first item
- [ ] Dropping a file while viewing another folder replaces the slideshow with that file's folder, starting at that file
- [ ] Dropping a folder while a video is playing stops that video's playback and sound
- [ ] Running the shipped `mediatagger` command with no path opens the window showing "Drop a folder or file here, or press `o` to open" instead of exiting with an error
- [ ] In the shipped `mediatagger` command started with no path, dropping a folder onto the window starts its slideshow at its first item
- [ ] A JPEG smaller than the window whose EXIF orientation says "rotate 90°" is shown upright at its decoded size (a landscape-stored photo tagged rotate 90° is drawn taller than wide)
- [ ] A JPEG larger than the window whose EXIF orientation says "rotate 90°" is shown upright when fitted to the window (drawn taller than wide, scaled down to fit)
- [ ] Acceptance: a screenshot of `mediatagger` started with no path on the Mac shows the "Drop a folder or file here, or press `o` to open" screen
