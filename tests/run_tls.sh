#!/bin/sh
# See run_tls.py. Runs every check on plain builds, then under AddressSanitizer/UBSan, then under ThreadSanitizer (with clang).
d="$(dirname "$0")"
python3 "$d/run_tls.py" && python3 "$d/run_tls.py" --san && \
  { ! command -v clang >/dev/null || CC=clang TSAN_OPTIONS="suppressions=$(cd "$d" && pwd)/tsan.supp" python3 "$d/run_tls.py" --tsan; }
