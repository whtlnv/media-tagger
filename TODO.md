# TODO

## Phase 30 — Del deletes a folder with everything in it

- [x] Forgetting what is gone of a folder removed from the drive takes the folder's row and the rows of the files and folders under it, at any depth, out of the library
- [x] Forgetting what is gone of a removed folder `Holidays` keeps the rows of a sibling whose name starts the same (`Holidays 2`) or matches it as a LIKE pattern (`Holidays_` vs `HolidaysX`)
- [x] Forgetting what is gone of a folder keeps the rows of a file under it that is still on the drive (and the folder's own row while the folder is still there)
- [ ] Forgetting what is gone of a removed folder removes its videos' chapter moments and the tag names nobody uses any more
- [ ] Pressing `Del` on a folder tile with two files in it asks `Delete folder "Photos" and the 2 files in it? It can't be undone.` (predicted-contradiction: test_window_delete.py::test_del_on_a_folder_tile_asks_nothing_and_leaves_the_folder_and_its_files — folder tiles now ask)
- [ ] Pressing `Del` on a folder tile with one file in it asks `… and the 1 file in it? …`
- [ ] Pressing `Del` on a folder tile with no files in it (only empty subfolders) asks `Delete empty folder "Photos"?`
- [ ] The folder question's count includes files in subfolders at any depth, and leaves out hidden files (`.DS_Store`, exFAT's `._*`)
- [ ] Pressing `Del` on a folder tile answered no keeps the folder, its files and their tags
- [ ] Pressing `Del` on a folder tile answered yes deletes the folder and everything in it from the drive
- [ ] Deleting a folder from a folder grid removes the folder's own tags and its files' tags from the drive's library
- [ ] After deleting a folder tile, the grid shows the parent folder without it, the cursor on the tile that took its place (the one before if it was last) and its tags in the status bar
- [ ] Deleting a folder whose subfolder won't let go of its files leaves what is left on the drive with its tags, removes the rows of what is gone, says `Couldn't delete — is the drive still connected?` and shows the grid again
- [ ] Deleting a folder whose library rows can't be removed still shows the parent without it and says tags couldn't be saved
- [ ] Pressing `Del` on a folder tile on a drive without a library asks nothing, keeps the folder and says `Can't delete here`
- [ ] The grid's cheat sheet row for `Del` reads `delete the picture, video or folder (asks first)`
