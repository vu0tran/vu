#!/bin/sh
# See run_pg_hostile.py: plain builds, then under AddressSanitizer/UBSan.
d="$(dirname "$0")"
python3 "$d/run_pg_hostile.py" && python3 "$d/run_pg_hostile.py" --san
