#!/bin/sh
# See run_norm.py: plain builds, then under AddressSanitizer/UBSan.
d="$(dirname "$0")"
python3 "$d/run_norm.py" && python3 "$d/run_norm.py" --san
