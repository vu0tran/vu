#!/bin/bash
# Command-line behavior: `check` never calls the C compiler, `run` builds unoptimized unless --release,
# `build` builds optimized unless --debug, and arguments after the file go to the program.
# A stand-in C compiler records the flags it was given, then hands off to the real one.
cd "$(dirname "$0")"
VU=${VU:-"$PWD/../vu"}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
unset VU_CACHE   # (these checks watch the C compiler being called)
export XDG_CACHE_HOME="$work/cache"   # (where vu run keeps binaries)
real_cc=${CC:-cc}
cat > "$work/cc" <<EOF
#!/bin/sh
echo "\$*" >> "$work/cc.log"
exec $real_cc "\$@"
EOF
chmod +x "$work/cc"
export CC="$work/cc"
pass=0; fail=0
check() {  # name, condition result (0 = ok), detail
  if [ "$2" -eq 0 ]; then pass=$((pass+1)); echo "ok    $1"; else fail=$((fail+1)); echo "FAIL  $1: $3"; fi
}
printf 'fn main():\n  print("{arg(1, 7) * 6}")\n' > "$work/ok.vu"
printf 'fn main():\n  var xs = [1]\n  for x in xs:\n    xs.push(x)\n' > "$work/bad.vu"

: > "$work/cc.log"; out=$($VU check "$work/ok.vu" 2>&1); rc=$?
[ $rc -eq 0 ] && [ -z "$out" ] && [ ! -s "$work/cc.log" ]; check "check: a correct file prints nothing, exits 0, no C compiler" $? "rc=$rc out=[$out] cc=$(cat "$work/cc.log")"

out=$($VU check "$work/bad.vu" 2>&1); rc=$?
want=$($VU build "$work/bad.vu" -o "$work/x" 2>&1)
[ $rc -eq 1 ] && [ "$out" = "$want" ]; check "check: an error exits 1 with the same message as build" $? "rc=$rc out=[$out]"

out=$($VU check "$work/ok.vu" --time 2>&1)
case "$out" in "vu: front end "*" ms") r=0 ;; *) r=1 ;; esac; check "check --time reports the front-end time" $r "[$out]"

: > "$work/cc.log"; out=$($VU run "$work/ok.vu" 2>&1)
[ "$out" = "42" ] && grep -q -- '-O0' "$work/cc.log" && ! grep -q -- '-O3' "$work/cc.log"; check "run: builds with -O0 by default" $? "out=[$out] cc=$(cat "$work/cc.log")"

: > "$work/cc.log"; out=$($VU run --release "$work/ok.vu" 2 2>&1)
[ "$out" = "12" ] && grep -q -- '-O3' "$work/cc.log"; check "run --release: builds with -O3" $? "out=[$out] cc=$(cat "$work/cc.log")"

out=$($VU run "$work/ok.vu" 5 2>&1)
[ "$out" = "30" ]; check "run: arguments after the file go to the program" $? "out=[$out]"

: > "$work/cc.log"; $VU build "$work/ok.vu" -o "$work/b" >/dev/null 2>&1
grep -q -- '-O3' "$work/cc.log"; check "build: builds with -O3 by default" $? "cc=$(cat "$work/cc.log")"

: > "$work/cc.log"; $VU build "$work/ok.vu" --debug -o "$work/b" >/dev/null 2>&1
grep -q -- '-O0' "$work/cc.log" && ! grep -q -- '-O3' "$work/cc.log"; check "build --debug: builds with -O0" $? "cc=$(cat "$work/cc.log")"

out=$($VU check "$work/missing.vu" 2>&1); rc=$?
[ $rc -eq 2 ] && [ "$out" = "vu: can't read '$work/missing.vu': No such file or directory" ]; check "a missing file: a clear message and exit 2" $? "rc=$rc out=[$out]"

out=$($VU check --json "$work" 2>&1); rc=$?
[ $rc -eq 2 ] && [ "$out" = "{\"type\": \"error\", \"file\": \"$work\", \"line\": 0, \"message\": \"can't read '$work': Is a directory\", \"source\": \"\"}" ]; check "a directory, with --json: one JSON error" $? "rc=$rc out=[$out]"

printf 'type Cfg:\n  Missing(key: Str)\n\nfn need(k: Str) -> Int throws Cfg:\n  fail Missing(k + "")\n\nfn main() throws Cfg:\n  let v = need("port")?\n  print("{v}")\n' > "$work/typed.vu"
out=$($VU run "$work/typed.vu" 2>&1); rc=$?
[ $rc -eq 1 ] && [ "$out" = "error: Missing(port)" ]; check "main fails with an enum value: its message, exit 1" $? "rc=$rc out=[$out]"

# vu new web NAME: the files, a starter that checks, and refusals that write nothing
out=$(cd "$work" && $VU new web demo-app 2>&1); rc=$?
[ $rc -eq 0 ] && for f in main.vu public/style.css Dockerfile .dockerignore .gitignore fly.toml railway.json README.md; do [ -s "$work/demo-app/$f" ] || exit 1; done \
  && grep -q 'app = "demo-app"' "$work/demo-app/fly.toml" && ! grep -q '@@' "$work/demo-app/README.md" "$work/demo-app/Dockerfile"
check "new web: writes the starter, with the name filled in" $? "rc=$rc out=[$out] $(ls -A "$work/demo-app" 2>&1)"
out=$($VU check "$work/demo-app/main.vu" 2>&1); check "new web: its main.vu checks" $? "$out"
before=$(ls -A "$work/demo-app" | wc -l); out=$(cd "$work" && $VU new web demo-app 2>&1); rc=$?
[ $rc -eq 1 ] && [ "$(ls -A "$work/demo-app" | wc -l)" = "$before" ]; check "new web: an existing folder is left alone (exit 1)" $? "rc=$rc out=[$out]"
for bad in "Demo" "1app" "a/b" "../x" "a b" ""; do
  out=$(cd "$work" && $VU new web "$bad" 2>&1); rc=$?; [ $rc -eq 2 ] || break
done
[ $rc -eq 2 ] && [ ! -e "$work/x" ]; check "new web: names that aren't lowercase letters, digits and '-' are refused" $? "bad=[$bad] rc=$rc out=[$out]"

# vu new api NAME
out=$(cd "$work" && $VU new api notes-api 2>&1); rc=$?
[ $rc -eq 0 ] && for f in main.vu migrations/001_init.sql Dockerfile .dockerignore .gitignore railway.json README.md; do [ -s "$work/notes-api/$f" ] || exit 1; done \
  && [ ! -e "$work/notes-api/public" ] && ! grep -q '@@\|public' "$work/notes-api/Dockerfile" && grep -q 'COPY migrations' "$work/notes-api/Dockerfile" && grep -q 'vu new api notes-api' "$work/notes-api/README.md" \
  && python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); assert d["deploy"]["healthcheckPath"] == "/health"' "$work/notes-api/railway.json"
check "new api: writes the starter, with the name filled in" $? "rc=$rc out=[$out] $(ls -A "$work/notes-api" 2>&1)"
out=$($VU check "$work/notes-api/main.vu" 2>&1); check "new api: its main.vu checks" $? "$out"
out=$(cd "$work" && $VU new cli x 2>&1); rc=$?
[ $rc -eq 2 ] && [ ! -e "$work/x" ]; check "new: a kind other than web or api is refused (exit 2)" $? "rc=$rc out=[$out]"

# --static: no dynamic loader needed
: > "$work/cc.log"; $VU build "$work/ok.vu" --static -o "$work/st" >/dev/null 2>&1
grep -q -- '-static' "$work/cc.log" && out=$("$work/st" 2>&1) && [ "$out" = "42" ] && python3 -c '
import struct, sys
d = open(sys.argv[1], "rb").read()
phoff, = struct.unpack_from("<Q", d, 32); size, n = struct.unpack_from("<HH", d, 54)
sys.exit(any(struct.unpack_from("<I", d, phoff + i * size)[0] == 3 for i in range(n)))' "$work/st"
check "build --static: linked with -static, runs, has no PT_INTERP (no dynamic loader)" $? "out=[$out] cc=$(cat "$work/cc.log")"

out=$($VU version 2>&1); rc=$?
[ $rc -eq 0 ] && [ "$out" = "vu 0.2.0" ]
check "version: prints the release" $? "rc=$rc out=[$out]"

printf 'fn f(xs: [Int]) -> Int:\n  var t = 0\n  for i in 0..xs.len: t += xs[i]\n  return t\nfn main():\n  print("{f([1, 2])}")\n' > "$work/ck.vu"
: > "$work/cc.log"; out=$($VU check --checks "$work/ck.vu" 2>&1); rc=$?
[ $rc -eq 0 ] && echo "$out" | grep -q "for i: 1 check on each pass" && echo "$out" | grep -q "'+' overflow" && [ ! -s "$work/cc.log" ]
check "check --checks: lists the checks each loop makes on every pass, without the C compiler" $? "rc=$rc out=[$out]"

printf 'fn main(os: Os) throws:\n  let s = os.read_stdin()?\n  print("{s.len}")\n' > "$work/rd.vu"
out=$(head -c 200000 /dev/zero | $VU run "$work/rd.vu" 2>&1); rc=$?
[ $rc -eq 0 ] && [ "$out" = "200000" ]; check "os.read_stdin(): all of standard input" $? "rc=$rc out=[$out]"

# --wasm refuses what WebAssembly (WASI) can't do, before any C compiler runs
printf 'fn main(net: Net) throws:\n  let c = net.connect("x", 1)?\n' > "$work/wn.vu"
: > "$work/cc.log"; out=$($VU build --wasm "$work/wn.vu" -o "$work/wn.wasm" 2>&1); rc=$?
[ $rc -eq 2 ] && echo "$out" | grep -q "need threads and sockets" && [ ! -e "$work/wn.wasm" ]
check "build --wasm: a program using the network is refused (exit 2)" $? "rc=$rc out=[$out]"
out=$($VU run --wasm "$work/ok.vu" 2>&1); rc=$?
[ $rc -eq 2 ] && echo "$out" | grep -q "builds a .wasm file"
check "run --wasm: refused, with how to run a .wasm file" $? "rc=$rc out=[$out]"

# vu run keeps each program's binary (in $XDG_CACHE_HOME/vu/run): a second run calls no C compiler,
# an edit rebuilds, and VU_RUN_CACHE=off always builds
printf 'fn main():\n  print("one")\n' > "$work/sc.vu"
out1=$($VU run "$work/sc.vu" 2>&1); : > "$work/cc.log"; out2=$($VU run "$work/sc.vu" 2>&1)
[ "$out1" = "one" ] && [ "$out2" = "one" ] && [ ! -s "$work/cc.log" ]; check "run: a second run uses the kept binary" $? "out=[$out1][$out2] cc=$(cat "$work/cc.log")"
printf 'fn main():\n  print("two")\n' > "$work/sc.vu"
: > "$work/cc.log"; out=$($VU run "$work/sc.vu" 2>&1)
[ "$out" = "two" ] && [ -s "$work/cc.log" ]; check "run: an edited program is built again" $? "out=[$out]"
: > "$work/cc.log"; out=$($VU run --release "$work/sc.vu" 2>&1)
[ "$out" = "two" ] && grep -q -- '-O3' "$work/cc.log"; check "run: other options keep their own binary" $? "out=[$out] cc=$(cat "$work/cc.log")"
: > "$work/cc.log"; out=$(VU_RUN_CACHE=off $VU run "$work/sc.vu" 2>&1)
[ "$out" = "two" ] && [ -s "$work/cc.log" ]; check "run: VU_RUN_CACHE=off always builds" $? "out=[$out]"
rm -rf "$work/cache"; $VU run "$work/sc.vu" >/dev/null; $VU run --release "$work/sc.vu" >/dev/null
n=$(ls "$work/cache/vu/run" | wc -l)
[ "$n" -eq 4 ]; check "run: two files kept for each program and options" $? "n=$n $(ls "$work/cache/vu/run")"
cp "$work/sc.vu" "$work/gone.vu"; $VU run "$work/gone.vu" >/dev/null; rm "$work/gone.vu"
n1=$(ls "$work/cache/vu/run" | wc -l); printf 'fn main():\n  print("3")\n' > "$work/sc.vu"; $VU run "$work/sc.vu" >/dev/null
n2=$(ls "$work/cache/vu/run" | wc -l)
[ "$n1" -eq 6 ] && [ "$n2" -eq 4 ]; check "run: a program whose file is gone is dropped" $? "n=$n1 then $n2"
for i in $(seq 1 66); do printf 'fn main():\n  print("%d")\n' $i > "$work/p$i.vu"; done
for i in $(seq 1 66); do $VU run "$work/p$i.vu" >/dev/null; done
n=$(ls "$work/cache/vu/run" | wc -l); out=$(cat "$work/cache/vu/run"/*.key | grep -c "/p1.vu$")
[ "$n" -eq 128 ] && [ "$out" -eq 0 ]; check "run: the 64 programs used last are kept" $? "n=$n p1=$out"

# vu check --caps: what main asks for, and no C compiler
printf 'fn main(fs: Fs, net: Net):\n  print("x")\n' > "$work/cap.vu"
: > "$work/cc.log"; out=$($VU check --caps "$work/cap.vu" 2>&1); rc=$?
[ $rc -eq 0 ] && echo "$out" | grep -q "^  fs   files" && echo "$out" | grep -q "^  net  the network" && ! echo "$out" | grep -q "^  os" && [ ! -s "$work/cc.log" ]
check "check --caps: lists main's capabilities, and nothing else" $? "rc=$rc out=[$out]"
out=$($VU check --caps "$work/ok.vu" 2>&1)
echo "$out" | grep -q "uses nothing outside itself"; check "check --caps: a program with none says so" $? "[$out]"
out=$($VU check --caps "$work/bad.vu" 2>&1); rc=$?
[ $rc -eq 1 ]; check "check --caps: a program with errors reports them (exit 1)" $? "rc=$rc [$out]"

echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
