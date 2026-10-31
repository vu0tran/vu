#!/bin/sh
# Packs a release for one platform, from the checked-out source:
#   packaging/release.sh VERSION PLATFORM MARCH       e.g. packaging/release.sh v0.3.0 linux-x64 x86-64-v2
# makes vu-VERSION-PLATFORM.tar.gz (vu, compiler/vuc, std/, README.md, llms.txt), the MCP servers'
# archives mcp-NAME-VERSION-PLATFORM.tar.gz, and sums-PLATFORM.txt with their SHA-256 sums.
#
# The compiler is compiled from compiler/vuc_seed.c (the C vuc made of itself, so it is exactly the
# tagged compiler) for a CPU every machine of the platform has (MARCH, empty for the compiler's
# default), not for the machine building it. The release workflow runs this for Linux in an Ubuntu
# 22.04 container, so the binary needs only glibc 2.34 or later.
set -eu
v="${1#v}"; platform="$2"; march="${3:-}"
cc="${CC:-cc}"
flags="-std=gnu11 -fwrapv -fno-math-errno -fno-trapping-math -ffp-contract=off -w -O3"
[ -n "$march" ] && flags="$flags -march=$march"
# shellcheck disable=SC2086
$cc $flags compiler/vuc_seed.c -o compiler/vuc -lm

# the compiler works: it checks, builds and runs a program with the standard library
export VU_STD="$PWD/std"
compiler/vuc version
# a tag's release: the compiler must say it is that version (the version in compiler/c5_build.vu)
if [ -n "${VU_CHECK_VERSION:-}" ] && [ "$(compiler/vuc version)" != "vu $v" ]; then
  echo "release: the tag is v$v but the compiler says '$(compiler/vuc version)'"; exit 1
fi
t=$(mktemp -d)
# (http: a module every release has; json was built in before 0.3)
printf 'import http\n\nfn main():\n  let r = http.Response(200, [], "ok")\n  print(r.body)\n' > "$t/hello.vu"
[ "$(compiler/vuc run "$t/hello.vu")" = ok ] || { echo "release: the compiler can't run a program"; exit 1; }
rm -rf "$t"

d="vu-$v-$platform"
rm -rf "$d"; mkdir -p "$d/compiler"
cp compiler/vuc "$d/compiler/"
cp -r std "$d/std"
for f in README.md llms.txt; do [ -f "$f" ] && cp "$f" "$d/"; done
for f in LICENSE LICENSE.md LICENSE.txt; do [ -f "$f" ] && cp "$f" "$d/"; done
cat > "$d/vu" <<'SH'
#!/bin/sh
# The Vu compiler. https://vulang.org
here="$(cd "$(dirname "$0")" && pwd)"
exec "$here/compiler/vuc" "$@"
SH
chmod +x "$d/vu"
tar czf "$d.tar.gz" "$d"
files="$d.tar.gz"

# the MCP servers, built by this compiler for the same CPU
for s in filesystem time fetch vu sqlite git; do
  [ -f "mcp/$s/main.vu" ] || continue
  m="mcp-$s-$v-$platform"
  rm -rf "$m"; mkdir "$m"
  VU_MARCH="$march" compiler/vuc build "mcp/$s/main.vu" -o "$m/mcp-$s"
  cp "mcp/$s/README.md" "$m/" 2>/dev/null || true
  tar czf "$m.tar.gz" "$m"
  files="$files $m.tar.gz"
done

# shellcheck disable=SC2086
if command -v sha256sum >/dev/null; then sha256sum $files; else shasum -a 256 $files; fi > "sums-$platform.txt"
cat "sums-$platform.txt"
