# TODO

- [x] Dropping a folder onto the viewer while the tag prompt is open closes the prompt without saving, so a later `Enter` cannot tag the previous item
- [x] The tag prompt's input reads as a text box: its style gives it a visible light border and a lighter translucent background than the overlays (the shown tags keep the overlays' look)
- [x] After the window is resized while the tag prompt is open, the prompt is still centred just above the status bar
- [ ] Opening a schema-version-1 library whose upgrade fails for a reason other than a read-only drive (e.g. the database is locked) raises the error instead of reporting no tags
- [ ] When a tag is removed from the last item that has it, its row in `tags` is deleted too
