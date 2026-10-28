#!/bin/bash
# The gate runs every suite with VU set to this script. It writes each `vu build` down (the folder, the
# settings that change the binary, and the arguments minus where the output goes) as one shell command
# in $VU_RECORD, for the next gate's prebuild.sh to replay, then runs the compiler under test, VU_REAL.
if [ "$1" = build ] && [ -n "$VU_RECORD" ]; then
  args=()
  skip=0
  for a in "${@:2}"; do
    if [ $skip = 1 ]; then skip=0; continue; fi
    case "$a" in
      -o|--emit-c) skip=1 ;;
      *) args+=("$a") ;;
    esac
  done
  # (one short line per write, so lines from suites running at the same time don't mix)
  printf 'cd %q && CC=%q VU_MARCH=%q VU_NO_VERSIONING=%q VU_STD=%q "$VU" build %s\n' \
    "$PWD" "${CC-}" "${VU_MARCH-}" "${VU_NO_VERSIONING-}" "${VU_STD-}" "$(printf '%q ' "${args[@]}")" >> "$VU_RECORD"
fi
exec "$VU_REAL" "$@"
