# TODO

Note for every cycle: put new tag-prompt and autocomplete viewer tests in `src/mediatagger/test_viewer_tag_prompt.py` (create it if missing; `test_viewer_library.py` is already over 1000 lines). Library-level tests go in `test_library.py`. Tests run offscreen and silent (`player_options={"ao": "null"}`), close every window/popup they open, and never touch real drives or `~`. Widget lifetimes: build the completer and its popup once per viewer, keep a reference on the viewer, and update its model in place; never create a completer, model or popup per keystroke. Garbage is collected only on the GUI thread (`collect_garbage_on_the_gui_thread` in viewer.py); keep it that way.

