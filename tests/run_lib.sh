#!/bin/sh
# vu build --lib: tests/lib/words.vu as a shared library and its header. A C program calls every
# exported function from one thread and then eight (tests/lib/driver.c), plain and with
# AddressSanitizer/LeakSanitizer/UBSan; Python calls it through ctypes against the same functions in
# Python (tests/lib/model.py), plain and (Linux) with AddressSanitizer preloaded; only the exported
# functions are visible; a panic ends the caller with the report; and what --lib refuses.
d="$(cd "$(dirname "$0")" && pwd)"
VU=${VU:-"$d/../vu"}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
pass=0; fail=0
check() {  # name, condition result (0 = ok), detail
  if [ "$2" -eq 0 ]; then pass=$((pass+1)); echo "ok    $1"; else fail=$((fail+1)); echo "FAIL  $1: $3"; fi
}
ext=so; [ "$(uname -s)" = Darwin ] && ext=dylib
cc=${CC:-cc}
mkdir "$work/plain" "$work/san"
cp "$d/lib/words.vu" "$work/plain/"
out=$(cd "$work/plain" && $VU build --lib words.vu 2>&1); rc=$?
[ $rc -eq 0 ] && [ -f "$work/plain/libwords.$ext" ] && [ -f "$work/plain/words.h" ]
check "build --lib: libwords.$ext and words.h next to the source" $? "rc=$rc $out $(ls "$work/plain")"

if [ "$ext" = dylib ]; then syms=$(nm -gU "$work/plain/libwords.dylib" | awk '{print $3}' | sed 's/^_//' | sort | tr '\n' ' ')
else syms=$(nm -D --defined-only "$work/plain/libwords.so" | awk '{print $3}' | sort | tr '\n' ' '); fi
want="add boom check_name count_words evens exclaim flip greet half mean next_byte nothing psum reverse_bytes scaled squares total "
[ "$syms" = "$want" ]; check "only the exported functions are visible" $? "[$syms]"

$cc -O1 -I"$work/plain" "$d/lib/driver.c" -o "$work/drv" -L"$work/plain" -lwords -Wl,-rpath,"$work/plain" -lpthread 2>"$work/cc.err"
out=$("$work/drv" 2>&1); rc=$?
[ $rc -eq 0 ] && echo "$out" | grep -q "checks passed"; check "C calls every function, from 1 and 8 threads" $? "rc=$rc $out $(head -5 "$work/cc.err")"

$VU build --lib --san "$d/lib/words.vu" -o "$work/san/libwords.$ext" 2>&1 | tail -3
$cc -fsanitize=address,undefined -g -I"$work/san" "$d/lib/driver.c" -o "$work/drvs" "$work/san/libwords.$ext" -Wl,-rpath,"$work/san" -lpthread 2>"$work/cc.err"
out=$("$work/drvs" 2>&1); rc=$?
[ $rc -eq 0 ] && echo "$out" | grep -q "checks passed" && ! echo "$out" | grep -q "Sanitizer"; check "the same with AddressSanitizer, LeakSanitizer and UBSan" $? "rc=$rc $(echo "$out" | head -20) $(head -5 "$work/cc.err")"

for s in 1 2 3; do
  out=$(python3 "$d/lib/model.py" "$work/plain/libwords.$ext" --seed $s 2>&1); rc=$?
  [ $rc -eq 0 ]; check "Python (ctypes) against the same functions in Python, seed $s" $? "$out"
done
if [ "$ext" = so ]; then
  asan=$($cc -print-file-name=libasan.so)
  if [ -f "$asan" ]; then
    out=$(LD_PRELOAD="$asan" ASAN_OPTIONS=detect_leaks=0 python3 "$d/lib/model.py" "$work/san/libwords.so" --rounds 500 2>&1); rc=$?
    [ $rc -eq 0 ] && ! echo "$out" | grep -q "Sanitizer"; check "Python with AddressSanitizer preloaded" $? "$(echo "$out" | head -20)"
  fi
fi

out=$(python3 -c "
import ctypes as C, sys
L = C.CDLL(sys.argv[1]); L.boom.restype = C.c_int64; L.boom.argtypes = [C.c_int64]
print(L.boom(1)); sys.stdout.flush(); L.boom(5); print('after the panic')" "$work/plain/libwords.$ext" 2>&1); rc=$?
[ $rc -eq 101 ] && echo "$out" | grep -q "^2$" && echo "$out" | grep -q "panic: index 5 out of bounds for a list of length 2" && ! echo "$out" | grep -q after
check "a panic ends the calling process (101) with the report" $? "rc=$rc $out"

printf 'fn main():\n  print("{exclaim("x")}")\nexport fn exclaim(s: Str) -> Str:\n  return s + "!"\n' > "$work/both.vu"
out=$($VU run "$work/both.vu" 2>&1)
[ "$out" = "x!" ]; check "a program can export functions and call them" $? "$out"
out=$(cd "$work" && $VU build --lib both.vu 2>&1); rc=$?
[ $rc -eq 0 ] && [ -f "$work/libboth.$ext" ]; check "a library may have a main (it isn't run)" $? "rc=$rc $out"

printf 'fn f() -> Int:\n  return 1\nfn main():\n  print("{f()}")\n' > "$work/none.vu"
out=$($VU build --lib "$work/none.vu" 2>&1); rc=$?
[ $rc -eq 2 ] && echo "$out" | grep -q "marked 'export fn'"; check "--lib without an export fn is refused" $? "rc=$rc $out"
printf 'fn feed(own c: Chan[Int]):\n  c.send(1)\nexport fn f() -> Int:\n  let c: Chan[Int] = chan(1)\n  spawn feed(c)\n  return 1\n' > "$work/tasks.vu"
out=$($VU build --lib "$work/tasks.vu" 2>&1); rc=$?
[ $rc -eq 2 ] && echo "$out" | grep -q "can't use tasks or channels"; check "--lib refuses tasks and channels" $? "rc=$rc $out"
printf 'export fn puts(s: Str) -> Int:\n  return s.len\n' > "$work/clash.vu"
out=$($VU build --lib "$work/clash.vu" -o "$work/libclash.$ext" 2>&1); rc=$?
[ $rc -eq 1 ] && echo "$out" | grep -q "already the C library's"; check "an export named like a C library function: told to rename it" $? "rc=$rc $(echo "$out" | tail -2)"
out=$($VU run --lib "$work/both.vu" 2>&1); rc=$?
[ $rc -eq 2 ]; check "--lib is only for build" $? "rc=$rc $out"

# the Python package template (packaging/python): pip builds the Vu code into the wheel
if python3 -m venv "$work/venv" >/dev/null 2>&1; then
  cp -r "$d/../packaging/python" "$work/pkg"
  out=$(cd "$work" && VU="$VU" "$work/venv/bin/pip" install -q ./pkg 2>&1); rc=$?
  if [ $rc -eq 0 ]; then
    out=$("$work/venv/bin/python" "$work/pkg/tests/test_fuzzy.py" 1000 2>&1); rc=$?
    [ $rc -eq 0 ]; check "the Python package template installs with pip and matches pure Python" $? "$out"
  elif echo "$out" | grep -q -i "network\|connection\|resolve"; then echo "skip  the Python package template (pip can't reach the package index)"
  else check "the Python package template installs with pip" 1 "$out"; fi
fi

echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
