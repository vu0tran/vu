#!/bin/sh
# See run_path.py: plain builds, then under AddressSanitizer/UBSan (fewer cases).
d="$(dirname "$0")"
python3 "$d/run_path.py" && N=3000 python3 "$d/run_path.py" --san
