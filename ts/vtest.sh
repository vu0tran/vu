#!/bin/sh
# vtsc's checked-in cases: each folder of vtests/ is checked (its .ts files, from the folder) and
# the output compared with the folder's expected.txt. The errors in expected.txt are tsc's (made
# with tsc and its tsconfig.json when there is one); "not checked" lines are vtsc's own.
#   ./vtest.sh VTSC            check every case
#   ./vtest.sh --save VTSC DIR  write DIR's expected.txt from VTSC's output (compare with tsc first)
# VTSC_LIB must name TypeScript's lib folder.
save=0
[ "$1" = "--save" ] && { save=1; shift; }
vtsc=$(cd "$(dirname "$1")" && pwd)/$(basename "$1"); shift
here=$(cd "$(dirname "$0")" && pwd)
[ $# -gt 0 ] || set -- "$here"/vtests/*/
fail=0
for d in "$@"; do
  out=$(cd "$d" && "$vtsc" $(ls *.ts | sort) 2>&1)
  if [ $save = 1 ]; then printf '%s\n' "$out" > "$d/expected.txt"; continue; fi
  if [ "$out" = "$(cat "$d/expected.txt")" ]; then echo "ok   $(basename "$d")"
  else echo "FAIL $(basename "$d")"; printf '%s\n' "$out" | diff "$d/expected.txt" - | head -20; fail=1; fi
done
exit $fail
