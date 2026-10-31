#!/bin/sh
# Installs Vu from its GitHub releases:
#   curl -fsSL https://vulang.org/install | sh
#   curl -fsSL https://vulang.org/install | VU_VERSION=0.2.0 sh        # a given version
# It puts the compiler and the standard library in ~/.vu (VU_HOME) and a `vu` command in ~/.local/bin
# (VU_BIN), after checking the archive against the release's SHA-256 sums. Running it again updates
# Vu. To uninstall: rm -rf ~/.vu ~/.local/bin/vu
# Platforms: Linux x86-64 and ARM64 (glibc 2.34 or later), macOS on Apple silicon.
# Vu builds programs through a C compiler, so one must be installed (cc, gcc or clang).
set -eu

repo="vu0tran/vu"
releases="${VU_RELEASES:-https://github.com/$repo/releases}"
home="${VU_HOME:-$HOME/.vu}"
bin="${VU_BIN:-$HOME/.local/bin}"

say() { printf 'vu: %s\n' "$*" >&2; }
die() { say "$*"; exit 1; }

if command -v curl >/dev/null 2>&1; then
  get() { curl -fsSL --retry 3 -o "$2" "$1"; }
  final_url() { curl -fsSLI --retry 3 -o /dev/null -w '%{url_effective}' "$1"; }
elif command -v wget >/dev/null 2>&1; then
  get() { wget -q -O "$2" "$1"; }
  final_url() { wget -q -S --spider "$1" 2>&1 | sed -n 's/^ *[Ll]ocation: *//p' | tail -1 | tr -d '\r'; }
else
  die "needs curl or wget"
fi

case "$(uname -s)/$(uname -m)" in
  Linux/x86_64 | Linux/amd64) platform=linux-x64 ;;
  Linux/aarch64 | Linux/arm64) platform=linux-arm64 ;;
  Darwin/arm64) platform=macos-arm64 ;;
  Darwin/x86_64)
    # a shell under Rosetta on Apple silicon says x86_64
    if [ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" = 1 ]; then platform=macos-arm64
    else die "there's no release for Intel Macs; build from source: git clone https://github.com/$repo && cd vu && ./vu version"; fi ;;
  *) die "there's no release for $(uname -s) $(uname -m); build from source: https://github.com/$repo" ;;
esac

version="${VU_VERSION:-}"
version="${version#v}"
if [ -z "$version" ]; then
  # .../releases/latest redirects to .../releases/tag/vX.Y.Z
  url=$(final_url "$releases/latest") || die "can't reach $releases"
  version="${url##*/tag/v}"
  case "$version" in "" | */* | *" "*) die "can't find the latest release at $releases" ;; esac
fi

name="vu-$version-$platform"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT INT TERM
say "downloading Vu $version for $platform"
get "$releases/download/v$version/$name.tar.gz" "$tmp/$name.tar.gz" || die "no $name.tar.gz in release v$version"
get "$releases/download/v$version/SHA256SUMS" "$tmp/SHA256SUMS" || die "no SHA256SUMS in release v$version"

want=$(awk -v f="$name.tar.gz" '$2 == f || $2 == "*" f { print $1 }' "$tmp/SHA256SUMS")
[ -n "$want" ] || die "$name.tar.gz isn't in the release's SHA256SUMS"
if command -v sha256sum >/dev/null 2>&1; then have=$(sha256sum "$tmp/$name.tar.gz" | awk '{print $1}')
else have=$(shasum -a 256 "$tmp/$name.tar.gz" | awk '{print $1}'); fi
[ "$have" = "$want" ] || die "$name.tar.gz doesn't match its SHA-256 sum (got $have, want $want); nothing was installed"

tar xzf "$tmp/$name.tar.gz" -C "$tmp"
[ -x "$tmp/$name/compiler/vuc" ] || die "the archive has no compiler/vuc"
"$tmp/$name/compiler/vuc" version >/dev/null 2>&1 || die "the compiler in $name.tar.gz doesn't run on this machine"

# replace the old install only once the new one is unpacked and runs
mkdir -p "$(dirname "$home")" "$bin"
rm -rf "$home.new"
mv "$tmp/$name" "$home.new"
rm -rf "$home.old"
[ -e "$home" ] && mv "$home" "$home.old"
mv "$home.new" "$home"
rm -rf "$home.old"

# a script, not a link: vuc finds std/ next to its own folder
cat > "$bin/vu.new" <<SH
#!/bin/sh
exec "$home/compiler/vuc" "\$@"
SH
chmod +x "$bin/vu.new"
mv "$bin/vu.new" "$bin/vu"

say "installed $("$bin/vu" version) in $home, the command in $bin/vu"
case ":$PATH:" in
  *":$bin:"*) ;;
  *) say "$bin isn't on your PATH: add  export PATH=\"$bin:\$PATH\"  to your shell's profile" ;;
esac
if ! command -v cc >/dev/null 2>&1 && ! command -v gcc >/dev/null 2>&1 && ! command -v clang >/dev/null 2>&1; then
  if [ "$platform" = macos-arm64 ]; then say "Vu needs a C compiler to build programs: run  xcode-select --install"
  else say "Vu needs a C compiler to build programs: install gcc (apt install gcc, dnf install gcc, apk add build-base)"; fi
fi
say "try it:  vu new app hello  or  vu run FILE.vu"
