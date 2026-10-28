#!/bin/sh
# See run_time_zones.py: plain builds, then under AddressSanitizer/UBSan.
d="$(dirname "$0")"
python3 "$d/run_time_zones.py" && python3 "$d/run_time_zones.py" --san
