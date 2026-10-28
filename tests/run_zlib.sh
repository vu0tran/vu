#!/bin/bash
# std/zlib against Python's zlib (see run_zlib.py).
cd "$(dirname "$0")" && python3 run_zlib.py "$@" && python3 run_zlib_compress.py
