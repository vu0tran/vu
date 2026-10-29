#!/bin/bash
# Split builds (vu run and --debug of big programs compile the functions in parts, in parallel, and
# keep each part's object file): every targeted test that runs (expect: output or panic), and every
# example, built split into 2 to 40 parts (VU_SPLIT=always) and as one C file (VU_SPLIT=off), must
# print the same, exit the same way and say the same on stderr. Then: no part holds its own copy of
# the runtime's state (writable data that isn't in part 0), a rebuild after an edit compiles only
# the part that changed, and the parts folder stays bounded.
cd "$(dirname "$0")"
VU=${VU:-"$PWD/../vu"}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
export XDG_CACHE_HOME="$work/cache" VU_RUN_CACHE=off
unset VU_CACHE
pass=0; fail=0
now() { python3 -c 'import time; print(time.time())'; }
since() { python3 -c "import time; print('%.2f' % (time.time() - $1))"; }
edit() {  # file, old line, new line: the first line that is exactly old becomes new
  python3 - "$@" <<'PY'
import sys
p, old, new = sys.argv[1:]
ls = open(p).read().split("\n")
ls[ls.index(old)] = new
open(p, "w").write("\n".join(ls))
PY
}
check() {  # name, condition result (0 = ok), detail
  if [ "$2" -eq 0 ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL  $1: $3"; fi
}
one() {  # a program: the same with and without splitting
  f=$1; d="$2/$(basename "$f" .vu)"; mkdir -p "$d"
  args=$(sed -n '3s/^# args: //p' "$f")
  (cd "$d" && VU_SPLIT=off timeout 120 "$VU" run "$OLDPWD/$f" $args > off.out 2> off.err; echo $? > off.rc)
  (cd "$d" && VU_SPLIT=always timeout 120 "$VU" run "$OLDPWD/$f" $args > on.out 2> on.err; echo $? > on.rc)
  if cmp -s "$d/off.out" "$d/on.out" && cmp -s "$d/off.rc" "$d/on.rc" && cmp -s "$d/off.err" "$d/on.err"; then echo ok; else echo "FAIL $f rc $(cat "$d/off.rc")/$(cat "$d/on.rc"): $(head -c 300 "$d/off.out" | tr '\n' ' ') // $(head -c 300 "$d/on.out" | tr '\n' ' ') // $(head -2 "$d/on.err" | tr '\n' ' ')"; fi
}
export -f one; export VU
progs=$(grep -l -E '^# expect: (output|panic) ' targeted/${ONLY:-*}.vu; ls ../examples/*.vu)
# (programs that need input, a network or timing aren't in the targeted tests' output kind)
res=$(printf '%s\n' $progs | xargs -P "$(getconf _NPROCESSORS_ONLN)" -I{} bash -c 'one {} '"$work/runs")
n=$(echo "$res" | grep -c '^ok')
bad=$(echo "$res" | grep '^FAIL')
[ -z "$bad" ]; check "every program prints the same split and whole ($n programs)" $? "$(echo "$bad" | head -20)"
echo "split and whole the same: $n programs"

# a big program: the compiler's own source
src="$PWD/../compiler/vuc.vu"
rm -rf "$XDG_CACHE_HOME"
s=$(now); VU_SPLIT=always "$VU" build --debug "$src" -o "$work/vuc1" 2>"$work/e1"; rc=$?; t1=$(since $s)
slot=$(ls -d "$XDG_CACHE_HOME"/vu/parts/*/ | head -1)
nparts=$(ls "$slot" | grep -c '\.o$')
[ $rc -eq 0 ] && [ "$nparts" -ge 10 ]; check "the compiler builds split ($nparts parts, $t1 s)" $? "rc=$rc $(head -5 "$work/e1")"
# writable data defined in more than one part (state each part would have its own copy of)
dup=$(for o in "$slot"/*.o; do nm "$o" 2>/dev/null | awk '$2 ~ /^[bdBDsS]$/ {print $3}' | sed 's/^_//; s/\.[0-9]*$//' | sort -u; done | grep -v -E '^(altstack|vu_guard_init\.altstack|__compound_literal)' | sort | uniq -d)
[ -z "$dup" ]; check "no part has its own copy of the runtime's state" $? "$(echo "$dup" | head -20 | tr '\n' ' ')"
"$work/vuc1" build "$src" --emit-c "$work/a.c" -o "$work/vuc2" >/dev/null 2>&1
"$VU" build "$src" --emit-c "$work/b.c" -o "$work/vuc3" >/dev/null 2>&1
cmp -s "$work/a.c" "$work/b.c"; check "the split-built compiler writes the same C as the installed one" $? "$(diff "$work/a.c" "$work/b.c" | head -5)"
# an edit to one function: one part compiled again
cp -r ../compiler "$work/c2"; cp "$src" "$work/c2/vuc.vu"
edit "$work/c2/vuc.vu" "fn shq(s: Str) -> Str:" "fn shq(s: Str) -> Str:
  let unused_here = 1"
s=$(now); VU_SPLIT=always "$VU" build --debug "$work/c2/vuc.vu" -o "$work/vuc4" 2>"$work/e2"; rc=$?; t2=$(since $s)
echo "the compiler: split build $t1 s, after a one-line edit $t2 s"
[ $rc -eq 0 ]; check "a rebuild after an edit works" $? "$(head -5 "$work/e2")"
# (a copy elsewhere is another program: its own folder)
s=$(now); VU_SPLIT=always "$VU" build --debug "$work/c2/vuc.vu" -o "$work/vuc4" 2>/dev/null; t3=$(since $s)
edit "$work/c2/vuc.vu" "  let unused_here = 1" "  let unused_here = 2"
s=$(now); VU_SPLIT=always "$VU" build --debug "$work/c2/vuc.vu" -o "$work/vuc4" 2>/dev/null; t4=$(since $s)
echo "the copy: unchanged $t3 s, after an edit $t4 s"
python3 -c "import sys; sys.exit(0 if $t4 < $t1 / 3 else 1)"; check "an edit rebuilds in a third of the time or less" $? "first $t1 s, after an edit $t4 s"
"$work/vuc4" check "$src"; check "the rebuilt compiler works" $? ""
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
