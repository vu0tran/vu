#!/bin/bash
# Packages: vu.pkg, vu get, vu.lock and capability grants, with local git repositories as sources.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
export VU_PKG_DIR="$work/cache"
pass=0; fail=0
check() {  # name, expected (substring of the output), command...
  local name=$1 want=$2; shift 2
  local got; got=$("$@" 2>&1)
  if printf '%s' "$got" | grep -qF -- "$want"; then pass=$((pass+1)); echo "ok    $name"
  else fail=$((fail+1)); echo "FAIL  $name"; echo "      want: $want"; echo "      got:  $(printf '%s' "$got" | head -5)"; fi
}
G="git -c user.name=t -c user.email=t@t -c init.defaultBranch=main -c advice.detachedHead=false"
repo() {  # name tag file content [file content...]: a repo with those files, tagged
  local d="$work/src/$1.git" tag=$2; shift 2
  mkdir -p "$d"; (cd "$d" && [ -d .git ] || $G init -q)
  while [ $# -gt 0 ]; do printf '%s\n' "$2" > "$d/$1"; shift 2; done
  (cd "$d" && $G add -A && $G commit -qm "$tag" && $G tag "$tag")
}
repo greet v1.0.0 greet.vu 'fn hello(n: Str) -> Str:
  return "hello " + n'
repo greet v1.1.0 greet.vu 'fn hello(n: Str) -> Str:
  return "hi " + n'
repo pinger v1.0.0 pinger.vu 'fn port(net: Net) -> Int:
  let l = net.listen(0) else return -1
  return net.port(l)'
repo spy v1.0.0 spy.vu 'fn peek(fs: Fs) -> Str:
  return fs.read("/etc/hostname") else ""'
repo cext v1.0.0 cext.vu 'extern "c.c":
  fn twice(ffi: Ffi, x: Int) -> Int
fn go(ffi: Ffi) -> Int:
  return twice(ffi, 2)' c.c 'static long long twice(long long x) { return 2 * x; }'
# a package that needs greet v1.1.0 and spy (granting it fs, which it doesn't have itself)
repo mid v1.0.0 mid.vu 'import greet
import spy
fn greet2(n: Str) -> Str:
  return greet.hello(n)' vu.pkg "need git+file://$work/src/greet.git v1.1.0
need git+file://$work/src/spy.git v1.0.0 fs"

app="$work/app"; mkdir -p "$app/lib"
printf 'fn shout(s: Str) -> Str:\n  return s.upper()\n' > "$app/lib/loud.vu"
cat > "$app/main.vu" <<'VU'
import greet
import pinger
import loud
fn main(net: Net):
  print(loud.shout(greet.hello("ann")))
  print("{pinger.port(net) > 0}")
VU
printf 'need git+file://%s/src/greet.git v1.0.0\nneed git+file://%s/src/pinger.git v1.0.0 net\nneed ./lib as loud\n' "$work" "$work" > "$app/vu.pkg"
cd "$app"
check "build before vu get" "isn't in vu.lock; run vu get" $VU run main.vu
check "vu get" "wrote" $VU get main.vu
check "lock lists both" "src/pinger.git v1.0.0" cat vu.lock
check "run with packages" "HELLO ANN
true" $VU run main.vu
# a changed file in the cache stops the build
f=$(ls -d "$VU_PKG_DIR"/*/*/src/greet.git@v1.0.0 2>/dev/null || find "$VU_PKG_DIR" -type d -name 'greet.git@v1.0.0' | head -1)
echo "# changed" >> "$f/greet.vu"
check "tampered package" "has changed since vu.lock was written" $VU run main.vu
sed -i '$ d' "$f/greet.vu"
check "restored package" "HELLO ANN" $VU run main.vu
# capabilities: pinger without net
sed -i 's/ v1.0.0 net$/ v1.0.0/' vu.pkg
check "capability not granted" "package 'pinger' isn't granted Net (vu.pkg)" $VU run main.vu
sed -i 's/pinger.git v1.0.0$/pinger.git v1.0.0 net/' vu.pkg
# ffi: an extern block needs ffi
printf 'import cext\nfn main(ffi: Ffi):\n  print("{cext.go(ffi)}")\n' > ffi.vu
printf 'need git+file://%s/src/cext.git v1.0.0\n' "$work" > "$work/ffiapp.pkg"
mkdir -p "$work/ffiapp" && cp ffi.vu "$work/ffiapp/main.vu" && cp "$work/ffiapp.pkg" "$work/ffiapp/vu.pkg"
(cd "$work/ffiapp" && $VU get main.vu >/dev/null 2>&1)
check "extern without ffi" "package 'cext' calls C (an extern block), but vu.pkg doesn't grant it ffi" $VU run "$work/ffiapp/main.vu"
sed -i 's/v1.0.0$/v1.0.0 ffi/' "$work/ffiapp/vu.pkg"
check "extern with ffi" "4" $VU run "$work/ffiapp/main.vu"
# transitive: mid asks for greet v1.1.0 (the higher version wins) and grants spy fs, which mid lacks
mkdir -p "$work/app2" && cd "$work/app2"
printf 'import mid\nfn main():\n  print(mid.greet2("bo"))\n' > main.vu
printf 'need git+file://%s/src/mid.git v1.0.0\nneed git+file://%s/src/greet.git v1.0.0\n' "$work" "$work" > vu.pkg
check "vu get (transitive)" "wrote" $VU get main.vu
check "highest version chosen" "src/greet.git v1.1.0" cat vu.lock
check "a package can't grant what it lacks" "package 'spy' isn't granted Fs (vu.pkg)" $VU run main.vu
sed -i 's|mid.git v1.0.0$|mid.git v1.0.0 fs|' vu.pkg
check "granted through" "hi bo" $VU run main.vu
# a missing tag, and a bad vu.pkg line
mkdir -p "$work/app3" && cd "$work/app3" && printf 'fn main():\n  print("x")\n' > main.vu
printf 'need git+file://%s/src/greet.git v9.9.9\n' "$work" > vu.pkg
check "missing version" "can't fetch" $VU get main.vu
printf 'need git+file://%s/src/greet.git v1.0.0 disk\n' "$work" > vu.pkg
check "unknown capability word" "unknown word 'disk'" $VU get main.vu
printf 'need git+file://%s/src/greet.git\n' "$work" > vu.pkg
check "no version" "needs a version" $VU get main.vu
# hostile sources: nothing git could take as an option or run as a command, from vu.pkg or from a
# dependency's own vu.pkg; and no symbolic links inside a package
mkdir -p "$work/app3" && cd "$work/app3"
# (scripts that would leave a mark if git ever ran them)
printf '#!/bin/sh\ntouch %s/pwned\n' "$work" > "$work/pwned.sh"; printf '#!/bin/sh\ntouch %s/pwned2\n' "$work" > "$work/pwned2.sh"; chmod +x "$work/pwned.sh" "$work/pwned2.sh"
printf 'import x\nfn main():\n  print("hi")\n' > main.vu
for src in "git+--upload-pack=$work/pwned.sh" "--upload-pack=touch://x" "git+ext::sh" "git+-c" "ftp://example.com/x"; do
  printf 'need %s v1.0.0\n' "$src" > vu.pkg
  check "source '$src' refused" "isn't a package source" $VU get main.vu
done
for ver in "v1/../../../escaped" "v1..2" "v1.0.0-../x" "v1;x"; do
  printf 'need git+file://%s/src/greet.git %s\n' "$work" "$ver" > vu.pkg
  check "version '$ver' refused" "needs a version" $VU get main.vu
done
[ -e "$work/escaped.tmp" ] || [ -e "$work/escaped" ] && { fail=$((fail+1)); echo "FAIL  a version led outside the cache"; }
printf 'need git+file://%s/src/greet.git v1.1.0\n' "$work" > vu.pkg
check "an ordinary version still works" "wrote" $VU get main.vu
repo evil v1.0.0 evil.vu 'fn f() -> Int:
  return 1' vu.pkg "need git+--upload-pack=$work/pwned2.sh v1.0.0"
printf 'need git+file://%s/src/evil.git v1.0.0\n' "$work" > vu.pkg
check "a dependency's hostile source refused" "isn't a package source" $VU get main.vu
if [ -e "$work/pwned" ] || [ -e "$work/pwned2" ]; then fail=$((fail+1)); echo "FAIL  a command ran"; else pass=$((pass+1)); echo "ok    no command ran"; fi
mkdir -p "$work/src/linky.git" && (cd "$work/src/linky.git" && $G init -q && printf 'fn f() -> Int:\n  return 1\n' > linky.vu && ln -s /etc/passwd secret.vu && ln -s . loop && $G add -A && $G commit -qm l && $G tag v1.0.0)
printf 'need git+file://%s/src/linky.git v1.0.0\n' "$work" > vu.pkg
check "a package with symbolic links refused" "contains symbolic links" $VU get main.vu
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
