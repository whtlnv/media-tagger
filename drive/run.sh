#!/bin/sh
# Starts MediaTagger from this drive with the computer's own python3 and the packages stored next to it.
# The drive is never written while the app runs: bytecode is precompiled when the drive is built or updated.
# Usage: sh run.sh [folder-or-file]
here=$(cd "$(dirname "$0")" && pwd -P)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$here/app:$here/lib-linux-aarch64-cp313" exec python3 -c "import mediatagger; mediatagger.main()" "$@"
