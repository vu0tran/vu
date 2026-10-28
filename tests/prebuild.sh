#!/bin/bash
# Builds, on every core at once, the binaries the gate's suites are about to build, into VU_CACHE, so the
# suites' own builds are copies. What to build is what the last gate's suites built (vu_record.sh wrote
# each down in $VU_CACHE/builds.list), plus run_loops' generated programs. Only a speedup: a binary is
# cached under a hash of everything it's made from, so a build this misses (a new test, a folder that's
# gone) or skips just happens in its suite as before.
cd "$(dirname "$0")" || exit 1
export VU=${VU:-"$PWD/../vu"}
[ -n "$VU_CACHE" ] || { echo "prebuild: set VU_CACHE"; exit 1; }
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
list="$VU_CACHE/builds.list"
: > "$work/jobs"
[ -f "$list" ] && sort -u "$list" > "$work/jobs"
# run_loops builds programs it generates in a folder of its own, by their names there (so their C is
# the same whatever the folder): the same programs, generated here
count=$(sed -n 's/^count=${1:-\([0-9]*\)}.*/\1/p' run_loops.sh)
count=${count:-300}
mkdir -p "$work/loops"
if python3 loops_gen.py 0 "$count" "$work/loops"; then
  for s in $(seq 0 $((count - 1))); do
    printf 'cd %q && "$VU" build p%s.vu\ncd %q && VU_NO_VERSIONING=1 "$VU" build p%s.vu\n' "$work/loops" "$s" "$work/loops" "$s" >> "$work/jobs"
  done
fi
n=$(wc -l < "$work/jobs")
t=$SECONDS
# each job gets its own output file; failures are the suites' business
awk -v w="$work" '{ printf "%s -o %s/o%d >/dev/null 2>&1\n", $0, w, NR }' "$work/jobs" |
  xargs -P "$(nproc)" -d '\n' -I{} bash -c '{}; true'
echo "$n builds in $((SECONDS - t)) s on $(nproc) cores"
