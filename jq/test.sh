#!/bin/sh
# Builds vjq and runs jq 1.7.1's own test suites (tests/*.test, copied from jq's source tree,
# MIT license) through `vjq --run-tests`, as jq's `make check` runs them through jq.
set -e
cd "$(dirname "$0")"
VU_SPLIT=off ../vu build --release vjq.vu -o vjq
cd tests
for t in jq man onig base64 optional; do
  printf '%-10s ' "$t.test"
  PAGER=less ../vjq -L modules --run-tests "$t.test" | tail -1
done
