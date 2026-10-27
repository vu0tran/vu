#!/bin/sh
# Builds compiler/vuc from vuc_seed.c with just the C compiler: the C that vuc made of itself the last
# time it was rebuilt (see build.sh). Nothing else is needed to get a working compiler.
cd "$(dirname "$0")" || exit 1
echo "vu: building the compiler from vuc_seed.c (once)" >&2
${CC:-cc} -std=gnu11 -fwrapv -fno-math-errno -fno-trapping-math -ffp-contract=off -w -O2 vuc_seed.c -o vuc.new -lm \
  && mv vuc.new vuc
