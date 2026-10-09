# TODO

- [ ] When listing a folder that passes the openable check fails with an I/O error (the test makes the folder listing raise `OSError(errno.EIO, "Input/output error")`, as an unplugged USB drive does), the viewer shows "Can't open <name>" instead of crashing, and dropping a readable folder afterwards still starts its slideshow
