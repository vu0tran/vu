#!/bin/sh
# Builds and packs one of the drop-in tools for one platform, from the checked-out source:
#   packaging/tools/build.sh TOOL VERSION PLATFORM [MARCH]
#     TOOL      vlint (oxlint) or vgolint (golangci-lint)
#     VERSION   0.1.0 (a leading v, vlint-v or vgolint-v is dropped)
#     PLATFORM  linux-x64, linux-arm64, darwin-x64 or darwin-arm64
#     MARCH     the CPU to build for (default: x86-64-v2 for x64, armv8-a for arm64), never native
# into dist/:
#   vlint:    vlint-VERSION-PLATFORM.tar.gz               (vlint-VERSION-PLATFORM/vlint, LICENSE, README.md)
#   vgolint:  vgolint-VERSION-GOOS-GOARCH.tar.gz          (vgolint-VERSION-GOOS-GOARCH/vgolint, ...;
#             named as golangci-lint names its archives: linux-amd64, darwin-arm64, ...)
#   sums-TOOL-PLATFORM.txt                                (the archive's SHA-256 sum)
#
# Linux binaries are linked statically (no glibc version floor: they run on any Linux with kernel
# 3.2 or later, musl distributions such as Alpine included). macOS binaries link only libSystem and
# run on macOS 12 or later (MACOSX_DEPLOYMENT_TARGET). Both are stripped.
# The compiler is built from compiler/vuc_seed.c first if compiler/vuc isn't there (./vu does that).
# CC picks the C compiler (as for vu build); a cross compiler works for Linux (CC=aarch64-linux-gnu-gcc,
# with STRIP=aarch64-linux-gnu-strip).
set -eu
tool="$1"; v="$2"; platform="$3"; march="${4:-}"
v="${v#vlint-}"; v="${v#vgolint-}"; v="${v#v}"
case "$platform" in
  linux-x64) goname=linux-amd64; os=linux ;;
  linux-arm64) goname=linux-arm64; os=linux ;;
  darwin-x64) goname=darwin-amd64; os=darwin ;;
  darwin-arm64) goname=darwin-arm64; os=darwin ;;
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
case "$tool" in
  vlint)
    # one C file (VU_SPLIT=off): the fastest binary
    (cd ts && VU_SPLIT=off ../vu build --release $static vlint.vu -o "$out/vlint")
    name="vlint-$v-$platform"; bin=vlint; readme=packaging/npm/vlint/README.md ;;
  vgolint)
    ./vu build --release $static golint/main.vu -o "$out/vgolint"
    name="vgolint-$v-$goname"; bin=vgolint; readme=golint/README.md ;;
  *) echo "build.sh: unknown tool $tool (vlint, vgolint)" >&2; exit 2 ;;
esac
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
cp LICENSE "$d/"
[ -f NOTICE ] && cp NOTICE "$d/"
cp "$readme" "$d/README.md"
(cd "$out" && tar czf "$root/dist/$name.tar.gz" "$name")
cd dist
if command -v sha256sum >/dev/null; then sha256sum "$name.tar.gz"; else shasum -a 256 "$name.tar.gz"; fi > "sums-$tool-$platform.txt"
cat "sums-$tool-$platform.txt"
rm -rf "$out"
