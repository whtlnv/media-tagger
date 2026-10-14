def fake_command(bin_dir, name, script):
    (bin_dir / name).write_text(f"#!/bin/sh\n{script}\n")
    (bin_dir / name).chmod(0o755)


def recorded_args(record):
    return record.read_bytes().split(b"\0")[:-1] if record.exists() else None
