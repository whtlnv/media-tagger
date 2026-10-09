# TODO

- [x] Dropping a folder onto the viewer while the tag prompt is open closes the prompt without saving, so a later `Enter` cannot tag the previous item
- [x] The tag prompt's input reads as a text box: its style gives it a visible light border and a lighter translucent background than the overlays (the shown tags keep the overlays' look)
- [x] After the window is resized while the tag prompt is open, the prompt is still centred just above the status bar
- [x] Opening a schema-version-1 library whose upgrade fails for a reason other than a read-only drive (e.g. the database is locked) raises the error instead of reporting no tags
- [x] When a tag is removed from the last item that has it, its row in `tags` is deleted too
- [x] Opening a folder on a drive whose `tags.db` is garbage bytes (so the library can't be opened) still shows the slideshow, and the status bar says "Library on <DRIVE> can't be opened — viewing only"
- [ ] On a drive whose library can't be opened, pressing `t` opens no tag prompt, shows "Tags can't be saved here", and leaves the drive's files unchanged
