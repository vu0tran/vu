#!/bin/bash
# vu fmt on every .vu file here: formatting twice changes nothing more, and every program (examples,
# valid and targeted output tests, the compiler itself) compiles to the same C before and after
# (#line directives aside: blank lines may go).
cd "$(dirname "$0")/.." || exit 1
VU=${VU:-"$PWD/vu"}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
cp -r examples std tests compiler "$work/"
pass=0; fail=0
files=$(cd "$work" && find . -name '*.vu' | sort)
(cd "$work" && $VU fmt $files >/dev/null)
for f in $files; do
  cp "$work/$f" "$work/once.vu"
  $VU fmt "$work/once.vu" >/dev/null
  if cmp -s "$work/$f" "$work/once.vu"; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL  $f: formatting it again changes it"; diff "$work/$f" "$work/once.vu" | head -6; fi
done
# the same C: programs that compile (their imports formatted too, in the same folders)
progs="compiler/vuc.vu $(ls examples/*.vu tests/valid/*.vu) $(grep -l '^# expect: output' tests/targeted/*.vu)"
for p in $progs; do
  # (only the C is compared: CC=true writes it and skips compiling it)
  ( cd "$(dirname "$p")" && CC=true $VU build "$(basename "$p")" --debug --emit-c "$work/a.c" -o "$work/a" ) >/dev/null 2>&1 || continue
  ( cd "$work/$(dirname "$p")" && CC=true $VU build "$(basename "$p")" --debug --emit-c "$work/b.c" -o "$work/b" ) >/dev/null 2>"$work/err"
  # (when formatting removed blank lines, line numbers in the C shift too: compare with numbers masked)
  mask=cat
  [ "$(wc -l < "$p")" = "$(wc -l < "$work/$p")" ] || mask="sed -E s/[0-9]+/N/g"
  if cmp -s <(grep -v '^ *#line' "$work/a.c" | $mask) <(grep -v '^ *#line' "$work/b.c" | $mask); then pass=$((pass+1))
  else fail=$((fail+1)); echo "FAIL  $p: different C after formatting $(head -c 200 "$work/err")"; diff <(grep -v '^ *#line' "$work/a.c") <(grep -v '^ *#line' "$work/b.c") | head -6; fi
done
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
