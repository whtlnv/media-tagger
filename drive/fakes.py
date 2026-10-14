def fake_command(bin_dir, name, script):
    (bin_dir / name).write_text(f"#!/bin/sh\n{script}\n")
    (bin_dir / name).chmod(0o755)
