# TODO

Note for every cycle: put new tag-prompt and autocomplete viewer tests in `src/mediatagger/test_viewer_tag_prompt.py` (create it if missing; `test_viewer_library.py` is already over 1000 lines). Library-level tests go in `test_library.py`. Tests run offscreen and silent (`player_options={"ao": "null"}`), close every window/popup they open, and never touch real drives or `~`. Widget lifetimes: build the completer and its popup once per viewer, keep a reference on the viewer, and update its model in place; never create a completer, model or popup per keystroke. Garbage is collected only on the GUI thread (`collect_garbage_on_the_gui_thread` in viewer.py); keep it that way.

- [x] In the tag prompt on a drive whose library has the tags `beach` and `bird`, typing `b` shows a suggestion popup listing `beach` and `bird`
- [x] In the tag prompt on a drive whose library has no tags yet, typing `b` shows no suggestion popup
- [x] In the tag prompt on a drive whose library has the tags `beach` and `bird`, typing `be` lists `beach` and not `bird`
- [x] Suggestions are ordered by how many items carry the tag: with `bird` on 3 items and `beach` on 1, typing `b` lists `bird` above `beach`
- [x] Suggestions are ordered by how many items carry the tag: with `beach` on 3 items and `bird` on 1, typing `b` lists `beach` above `bird`
- [x] Suggestions with the same item count are listed alphabetically: with `bird` and `beach` on 2 items each, typing `b` lists `beach` above `bird`
- [x] Suggestion matching ignores case: typing `BE` lists `beach`
- [x] Suggestions complete the last space-separated word: typing `beach fam` with `family` in the library lists `family`
- [x] Typing a namespace prefix lists every tag under it at any depth: typing `people:` lists `people:ana` and `people:luis:jr`, and not `place:mexico`
- [x] Tags the current item already has are not suggested for adding: on an item tagged `sunset`, with `summer` also in the library, typing `s` lists `summer` and not `sunset`
- [x] A word starting with `-` suggests from the current item's own tags: on an item tagged `sunset`, with `summer` also in the library, typing `-s` lists `sunset` and not `summer`
- [x] Words already entered in the prompt are not suggested again: typing `beach b` lists `bird` and not `beach`
- [x] Suggestions come from the current drive's library: after dropping a folder from a second drive whose library has only `zebra`, typing `b` shows no popup and typing `z` lists `zebra`
- [x] A tag saved from the prompt is suggested the next time the prompt opens: after saving `zebra` on one item, opening the prompt on the next item and typing `z` lists `zebra`
- [x] In the suggestion popup, `↓` twice highlights the second suggestion and `↑` then highlights the first
- [x] `Tab` accepts the highlighted suggestion, replacing only the word being typed: `beach fam`, `↓`, `Tab` leaves `beach family` in the prompt and closes the popup
- [x] `Enter` accepts the highlighted suggestion without saving: `beach fam`, `↓`, `Enter` leaves `beach family` in the open prompt and the item's tags unchanged
  - note: `Enter` accepts only when a suggestion is highlighted (via `↓`/`↑`). With the popup showing but nothing highlighted, `Enter` saves as before — `test_on_a_file_tagged_beach_family_typing_minus_family_in_the_tag_prompt_and_pressing_enter_leaves_it_tagged_only_beach` must keep passing (no contradiction).
- [x] Accepting a removal suggestion keeps the `-`: on an item tagged `sunset`, `-s`, `↓`, `Tab` leaves `-sunset` in the prompt
- [x] `Esc` with the suggestion popup open closes only the popup: the prompt stays open with its text and the app keeps running
- [x] Accepting a suggestion for the only word in the prompt leaves no leading space: `fam`, `↓`, `Tab` leaves exactly `family` in the prompt
- [x] `Esc` after the popup has been closed cancels the prompt, leaving the item's tags unchanged
- [x] `Enter` with no suggestion popup showing saves the prompt's text: `beach fam`, `Esc`, `Enter` adds `beach` and `fam` to the item
- [x] On a video item with the suggestion popup open, `↓` and `↑` move the highlight and do not seek the video
- [x] The suggestion popup over a white image shows light text on a dark background, as the overlays do
- [x] The suggestion popup opens above the prompt and lies entirely inside the window, even with more suggestions than fit below the prompt
- [ ] With 5,000 tags in the library, each keystroke in the tag prompt updates the suggestions in under 50 ms
- [ ] When saving the prompt fails with `sqlite3.Error` from the library, the prompt stays open with its text and the status bar says "Couldn't save tags — is the drive still connected?"
- [ ] When saving the prompt fails with `OSError` from the library, the prompt stays open with its text and the status bar says "Couldn't save tags — is the drive still connected?"
- [ ] Running the shipped `mediatagger <folder>` command on a drive whose library has `beach`, pressing `t` and typing `b` shows the suggestion popup listing `beach` (the test's driver script treats a temp folder as the mount point)
