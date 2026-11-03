#!/bin/sh
# Builds and packs one of the drop-in tools for one platform, from the checked-out source:
#   packaging/tools/build.sh TOOL VERSION PLATFORM [MARCH]
#     TOOL      vlint (oxlint), vgolint (golangci-lint), vsc (ShellCheck), vjq (jq) or vknip (knip)
#     VERSION   0.1.0 (a leading v or TOOL-v is dropped)
#     PLATFORM  linux-x64, linux-arm64, darwin-x64 or darwin-arm64
#     MARCH     the CPU to build for (default: x86-64-v2 for x64, armv8-a for arm64), never native
# into dist/ (each archive holds one folder, named as the archive, with the binary, LICENSE, NOTICE
# and README.md; the original's name is a symbolic link to the binary):
#   vlint:    vlint-VERSION-PLATFORM.tar.gz               vlint
#   vgolint:  vgolint-VERSION-GOOS-GOARCH.tar.gz          vgolint (golangci-lint's names: linux-amd64, darwin-arm64, ...)
#   vsc:      vsc-vVERSION.OS.ARCH.tar.xz                 vsc, shellcheck -> vsc (ShellCheck's names:
#             linux.x86_64, linux.aarch64, darwin.x86_64, darwin.aarch64)
#   vjq:      vjq-VERSION-OS-ARCH.tar.gz                  vjq, jq -> vjq (jq's names: linux-amd64, linux-arm64,
#             macos-amd64, macos-arm64), and the bare binary as jq-OS-ARCH (jq's release asset names)
#   vknip:    vknip-VERSION-PLATFORM.tar.gz               vknip, knip -> vknip
#   sums-TOOL-PLATFORM.txt                                the SHA-256 sums of what was made
#
# Linux binaries are linked statically (no glibc version floor: they run on any Linux with kernel
# 3.2 or later, musl distributions such as Alpine included). macOS binaries link only libSystem and
# run on macOS 12 or later (MACOSX_DEPLOYMENT_TARGET). Both are stripped.
# The compiler is built from compiler/vuc_seed.c first if compiler/vuc isn't there (./vu does that).
# CC picks the C compiler (as for vu build); a cross compiler works for Linux (CC=aarch64-linux-gnu-gcc,
# with STRIP=aarch64-linux-gnu-strip).
set -eu
tool="$1"; v="$2"; platform="$3"; march="${4:-}"
v="${v#"$tool"-}"; v="${v#v}"
case "$platform" in
  linux-x64) goname=linux-amd64; scname=linux.x86_64; jqname=linux-amd64; os=linux ;;
  linux-arm64) goname=linux-arm64; scname=linux.aarch64; jqname=linux-arm64; os=linux ;;
  darwin-x64) goname=darwin-amd64; scname=darwin.x86_64; jqname=macos-amd64; os=darwin ;;
  darwin-arm64) goname=darwin-arm64; scname=darwin.aarch64; jqname=macos-arm64; os=darwin ;;
  *) echo "build.sh: unknown platform $platform (linux-x64, linux-arm64, darwin-x64, darwin-arm64)" >&2; exit 2 ;;
esac
if [ -z "$march" ]; then
  case "$platform" in *-x64) march=x86-64-v2 ;; *) march=armv8-a ;; esac
fi
[ "$march" = native ] && { echo "build.sh: -march=native makes a binary for this machine only" >&2; exit 2; }

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"
./vu version >/dev/null
mkdir -p dist
out="$root/dist/.build-$tool-$platform"
rm -rf "$out"; mkdir -p "$out"

static=""
if [ "$os" = linux ]; then static="--static"; else export MACOSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-12.0}"; fi
export VU_MARCH="$march"
alias=""; ext=tar.gz; bare=""
case "$tool" in
  vlint)
    # one C file (VU_SPLIT=off): the fastest binary
    (cd ts && VU_SPLIT=off ../vu build --release $static vlint.vu -o "$out/vlint")
    name="vlint-$v-$platform"; readme=packaging/npm/vlint/README.md ;;
  vgolint)
    ./vu build --release $static golint/main.vu -o "$out/vgolint"
    name="vgolint-$v-$goname"; readme=golint/README.md ;;
  vsc)
    ./vu build --release $static shellcheck/vsc.vu -o "$out/vsc"
    name="vsc-v$v.$scname"; readme=shellcheck/README.md; alias=shellcheck; ext=tar.xz ;;
  vjq)
    (cd jq && VU_SPLIT=off ../vu build --release $static vjq.vu -o "$out/vjq")
    name="vjq-$v-$jqname"; readme=jq/README.md; alias=jq; bare="jq-$jqname" ;;
  vknip)
    ./vu build --release $static knip/vknip.vu -o "$out/vknip"
    name="vknip-$v-$platform"; readme=knip/README.md; alias=knip ;;
  *) echo "build.sh: unknown tool $tool (vlint, vgolint, vsc, vjq, vknip)" >&2; exit 2 ;;
esac
bin="$tool"
"${STRIP:-strip}" "$out/$bin"

# what it needs where it runs
if [ "$os" = linux ]; then
  if command -v file >/dev/null; then file "$out/$bin"; fi
  if ldd "$out/$bin" 2>&1 | grep -q '=>'; then echo "build.sh: $bin isn't static:" >&2; ldd "$out/$bin" >&2; exit 1; fi
else
  otool -L "$out/$bin"
  if otool -L "$out/$bin" | tail -n +2 | grep -v '/usr/lib/libSystem\|/usr/lib/libc++' | grep -q .; then
    echo "build.sh: $bin links more than the system's libraries" >&2; exit 1
  fi
fi

d="$out/$name"
mkdir -p "$d"
cp "$out/$bin" "$d/"
[ -n "$alias" ] && ln -s "$bin" "$d/$alias"
cp LICENSE "$d/"
[ -f NOTICE ] && cp NOTICE "$d/"
cp "$readme" "$d/README.md"
case "$ext" in
  tar.gz) (cd "$out" && tar czf "$root/dist/$name.$ext" "$name") ;;
  tar.xz)
    # (xz where it's installed; else tar's own: macOS's bsdtar has liblzma built in)
    if command -v xz >/dev/null; then (cd "$out" && tar cf - "$name" | xz -9 > "$root/dist/$name.$ext")
    else (cd "$out" && tar cJf "$root/dist/$name.$ext" "$name"); fi ;;
esac
files="$name.$ext"
if [ -n "$bare" ]; then
  cp "$out/$bin" "$root/dist/$bare"
  files="$files $bare"
fi
cd dist
# shellcheck disable=SC2086
if command -v sha256sum >/dev/null; then sha256sum $files; else shasum -a 256 $files; fi > "sums-$tool-$platform.txt"
cat "sums-$tool-$platform.txt"
rm -rf "$out"
