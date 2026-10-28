#!/bin/sh
# See run_http_client.py: plain builds, then under AddressSanitizer/UBSan.
d="$(dirname "$0")"
python3 "$d/run_http_client.py" && python3 "$d/run_http_client.py" --san
