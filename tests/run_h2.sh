#!/bin/sh
# See run_h2.py: plain builds, then under AddressSanitizer/UBSan.
d="$(dirname "$0")"
python3 "$d/run_h2.py" && python3 "$d/run_h2.py" --san
