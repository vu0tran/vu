#!/bin/sh
# vtsc's checked-in cases: each folder of vtests/ is checked (its .ts files, from the folder) and
# the output compared with the folder's expected.txt. The errors in expected.txt are tsc's (made
# with tsc and its tsconfig.json when there is one); "not checked" lines are vtsc's own.
#   VTSC_LIB=LIBDIR ./vtest.sh VTSC              check every case
#   VTSC_LIB=LIBDIR ./vtest.sh VTSC DIR...       check these cases
#   VTSC_LIB=LIBDIR ./vtest.sh --save VTSC DIR   write DIR's expected.txt from VTSC's output (compare with tsc first)
# VTSC_LIB must name TypeScript's lib folder: the one vlint carries (ltslib.vu's TSLIB_HASH, which
# vlint writes to $XDG_CACHE_HOME/vlint/tslib-HASH), checked here; another lib is refused.
#
# Hermetic: the cases are copied to a fresh folder under /tmp and checked there, so nothing outside
# a case's folder is read. (Given files, vtsc takes every @types package from the current folder up,
# as tsc does: a node_modules above the checkout, ~/node_modules/@types/node, changed globals,
# narrowing and packages. A case's absolute path is in some messages (typeof import("...")), and
# how long it is decides where tsc elides: under a long path esm-default-import-cjs isn't checked.)
# A node_modules in any folder above the copy is refused. The test list and each case's files are
# in C order. The output is the same from any checkout, cwd and environment.
export LC_ALL=C
save=0
[ "$1" = "--save" ] && { save=1; shift; }
[ $# -ge 1 ] || { echo "usage: VTSC_LIB=LIBDIR $0 [--save] VTSC [CASE_DIR...]" >&2; exit 2; }
vtsc=$(cd "$(dirname "$1")" && pwd)/$(basename "$1"); shift
[ -x "$vtsc" ] || { echo "vtest: $vtsc isn't an executable" >&2; exit 2; }
here=$(cd "$(dirname "$0")" && pwd)
[ -n "$VTSC_LIB" ] && [ -f "$VTSC_LIB/lib.es5.d.ts" ] || { echo "vtest: VTSC_LIB must name TypeScript's lib folder (lib.es5.d.ts in it)" >&2; exit 2; }
want=$(sed -n 's/^const TSLIB_HASH = "\(.*\)"$/\1/p' "$here/ltslib.vu")
got=$(python3 -I -c '
import hashlib, os, sys
d = sys.argv[1]; h = hashlib.sha256()
for n in sorted(n for n in os.listdir(d) if n.endswith(".d.ts")):
    h.update(n.encode() + b"\0" + open(os.path.join(d, n), encoding="utf8").read().encode("utf8") + b"\0")
print(h.hexdigest()[:16])' "$VTSC_LIB")
[ "$got" = "$want" ] || { echo "vtest: VTSC_LIB's lib files hash to $got, not ltslib.vu's $want (the lib the expected outputs were made with)" >&2; exit 2; }
export VTSC_LIB=$(cd "$VTSC_LIB" && pwd -P)
# (the environment variables that change what vtsc does, unset; VTEST_ENV=keep keeps them: VTSC_FILE_TIME)
[ "$VTEST_ENV" = keep ] || for v in $(env | sed -n 's/^\(VTSC_[A-Z0-9_]*\)=.*/\1/p'); do [ "$v" = VTSC_LIB ] || unset "$v"; done
[ $# -gt 0 ] || set -- "$here"/vtests/*/
run=$(mktemp -d /tmp/vtest.XXXXXX) || exit 2
run=$(cd "$run" && pwd -P)
trap 'rm -rf "$run"' EXIT
trap 'exit 130' INT TERM
p=$(dirname "$run")
while :; do
  [ -e "$p/node_modules" ] && { echo "vtest: $p/node_modules is above the cases' copy: they wouldn't be hermetic" >&2; exit 2; }
  [ "$p" = / ] && break
  p=$(dirname "$p")
done
fail=0; nok=0; nfail=0
for d in "$@"; do
  src=$(cd "$d" && pwd)
  name=$(basename "$src")
  cp -R "$src" "$run/$name"
  # (the folder's absolute path, in messages that name a module, left out)
  ad="$run/$name"
  # (a folder with a file named use-project: checked as its tsconfig.json's project)
  if [ -f "$ad/use-project" ]; then out=$(cd "$ad" && PWD="$ad" "$vtsc" -p tsconfig.json 2>&1 | sed "s|$ad/||g")
  else out=$(cd "$ad" && PWD="$ad" "$vtsc" $(ls *.ts | sort) 2>&1 | sed "s|$ad/||g"); fi
  rm -rf "$ad"
  if [ $save = 1 ]; then printf '%s\n' "$out" > "$src/expected.txt"; continue; fi
  if [ "$out" = "$(cat "$src/expected.txt")" ]; then echo "ok   $name"; nok=$((nok + 1))
  else echo "FAIL $name"; printf '%s\n' "$out" | diff "$src/expected.txt" - | head -20; fail=1; nfail=$((nfail + 1)); fi
done
[ $save = 1 ] || echo "vtest: $nok ok, $nfail FAIL"
exit $fail
