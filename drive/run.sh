#!/bin/sh
here=$(cd "$(dirname "$0")" && pwd -P)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$here/app:$here/lib-linux-aarch64-cp313" exec python3 -c "import mediatagger; mediatagger.main()" "$@"
