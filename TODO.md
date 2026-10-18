# TODO

## Phase 29 — Del deletes a picture or video from the grid

- [x] Forgetting a tagged file in the library leaves it with no tags, and a tag name only it used is gone from the library's tags
- [x] Forgetting a video in the library removes its chapter moments
- [x] Pressing `Del` in a folder grid on an image tile, answering yes to the question, deletes the file from the drive
- [x] Pressing `Del` in a folder grid on an image tile asks `Delete "IMG_1.png"? It can't be undone.`
- [x] Pressing `Del` in a folder grid on an image tile, answering no, keeps the file and its tags
- [x] Deleting a tagged image from a folder grid removes its tags from the drive's library
- [x] After deleting a tile from a folder grid, the grid shows the folder without it, the cursor on the tile that took its place
- [x] After deleting the last tile of a folder grid, the cursor is on the tile before it
- [x] After deleting a tile from a folder grid, the status bar shows the tags of the tile now under the cursor
- [x] Pressing `Del` in the grid of an empty folder asks nothing and raises nothing
- [x] Pressing `Del` in the viewer asks nothing and leaves the file on the drive
- [x] Pressing `Del` in a folder grid where tags can't be saved asks nothing, keeps the file and flashes `Can't delete here`
- [x] Pressing `Del` on a file the drive refuses to delete shows `Couldn't delete — is the drive still connected?` and leaves its tags in the library
- [x] Pressing `Del` on a folder tile, or in search results, asks nothing and deletes nothing (Phases 30–31)
- [x] Without a fake answer, the window's delete question is a modal whose Enter deletes the file and whose Esc keeps it
- [x] The window's delete question's focused default button reads Delete, and its other button Keep
- [ ] The grid's cheat sheet lists `Del` as deleting the file
