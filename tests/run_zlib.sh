#!/bin/bash
# std/zlib against Python's zlib (see run_zlib.py).
cd "$(dirname "$0")" && exec python3 run_zlib.py "$@"
