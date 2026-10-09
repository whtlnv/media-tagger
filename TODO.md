# TODO

- [x] Opening the viewer on a folder path that doesn't exist shows a centred "Can't open <name>" message instead of crashing
- [x] Opening the viewer on a file path that doesn't exist (e.g. `does_not_exist.jpg` in a missing folder) shows "Can't open does_not_exist.jpg" instead of crashing
- [ ] Opening the viewer on a folder that can't be read (permission denied; the test chmods a temp folder to 000 and restores it afterwards) shows "Can't open <name>" instead of crashing
- [ ] Dropping a folder that doesn't exist while a video is showing stops the video, hides the video surface and shows "Can't open <name>"
- [ ] Dropping a folder that doesn't exist while the `i` overlay is shown hides the overlay
- [ ] After "Can't open <name>" is shown, dropping a readable folder onto the window starts that folder's slideshow at its first item
- [ ] After "Can't open <name>" is shown, pressing `o` and choosing a readable folder in the picker starts that folder's slideshow
- [ ] Running the shipped `mediatagger /no/such/path` command keeps running and shows "Can't open path" instead of exiting with an error
- [ ] The launch screen text reads "Drop a folder or file here, or press o to open", with no backticks around the o
  - predicted-contradiction: `src/mediatagger/test_viewer_open.py::test_a_viewer_opened_with_no_path_shows_only_the_launch_text` — asserts: the launch screen shows exactly "Drop a folder or file here, or press `o` to open" (with backticks) — retired-by: "reads \"Drop a folder or file here, or press o to open\", with no backticks around the o"
