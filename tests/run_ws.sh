#!/bin/sh
# See run_ws.py: plain builds, then under AddressSanitizer/UBSan.
d="$(dirname "$0")"
python3 "$d/run_ws.py" && python3 "$d/run_ws.py" --san
