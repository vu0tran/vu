#!/bin/bash
# Loop versioning (hoisted index checks and tried copies, compiler/c4_stmt.vu): random programs from
# loops_gen.py, each built with versioning and without it (VU_NO_VERSIONING=1), must print the same
# and stop the same way (message, line, exit status).
#   tests/run_loops.sh [COUNT] [FIRST_SEED]
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
count=${1:-300}; first=${2:-0}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
python3 loops_gen.py "$first" $((first + count)) "$work" || exit 1
pass=0; fail=0
for s in $(seq "$first" $((first + count - 1))); do
  f="p$s.vu"   # (built by its name in $work, so the binary is the same as prebuild.sh's)
  if ! (cd "$work" && "$VU" build "$f" -o "$work/v" >"$work/err" 2>&1) || ! (cd "$work" && VU_NO_VERSIONING=1 "$VU" build "$f" -o "$work/n" >>"$work/err" 2>&1); then
    fail=$((fail+1)); echo "FAIL  seed $s doesn't build: $(head -3 "$work/err")"; continue
  fi
  a=$(cd "$work" && timeout 30 ./v 2>&1; echo "exit $?")
  b=$(cd "$work" && timeout 30 ./n 2>&1; echo "exit $?")
  if [ "$a" == "$b" ]; then pass=$((pass+1))
  else fail=$((fail+1)); echo "FAIL  seed $s"; echo "      versioned: $(echo "$a" | tr '\n' ' ' | cut -c1-300)"; echo "      plain:     $(echo "$b" | tr '\n' ' ' | cut -c1-300)"; fi
done
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
