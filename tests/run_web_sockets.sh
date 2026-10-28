#!/bin/sh
# See run_web_sockets.py: plain builds, then under AddressSanitizer/UBSan.
d="$(dirname "$0")"
python3 "$d/run_web_sockets.py" && python3 "$d/run_web_sockets.py" --san
