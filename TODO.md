# TODO

## Phase 31 — Del in search results

- [x] `Del` on a file in search results, answered yes, deletes the file from the drive and its rows from the library
  - predicted-contradiction: test_window_delete.py::test_del_on_a_file_in_search_results_asks_nothing_and_leaves_the_file_on_the_drive — retired by "Del on a file in search results … deletes the file"
- [x] After deleting a file from search results, the results of the same search are shown without it (breadcrumb kept), the cursor on the result that took its place, its tags in the status bar
- [ ] After deleting the last result, the cursor is on the result before it
- [ ] `Esc` from the results after deleting a result that was in the folder searched from shows that folder without it
- [ ] Coming back to the results from a slideshow opened after a delete puts the cursor on the slideshow's current file
- [ ] `Del` on a folder in search results, answered yes, deletes the folder and the rows under it, and it leaves the results
- [ ] `Del` on a missing (`?`) result asks `Forget "IMG_2.png"? Its tags are removed.`
- [ ] A missing result answered yes loses its library rows and leaves the results
- [ ] The real question for a missing result has a **Forget** button (default) and **Keep**
