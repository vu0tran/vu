#!/bin/sh
# See run_sqlite.py. Plain builds, then under AddressSanitizer/UBSan.
d="$(dirname "$0")"
python3 "$d/run_sqlite.py" && python3 "$d/run_sqlite.py" --san
