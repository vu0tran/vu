#!/bin/sh
# Installs vgolint (golangci-lint in Vu) from this repository's GitHub releases, with golangci-lint's
# installer's interface:
#   curl -sSfL https://raw.githubusercontent.com/vu0tran/vu/main/golint/install.sh | sh -s -- -b $(go env GOPATH)/bin v0.1.0
#
# Usage: install.sh [-b BINDIR] [-d] [-f] [-n] [TAG]
#   -b  where to put the binary (default ./bin, as golangci-lint's installer)
#   -d  debug output
#   -f  replace a golangci-lint that is already in BINDIR (by default it is left alone)
#   -n  install vgolint only, without the golangci-lint name
#   TAG a vgolint release: v0.1.0, 0.1.0 or vgolint-v0.1.0 (default: the latest vgolint release)
#
# It installs BINDIR/vgolint and, so that scripts calling golangci-lint keep working, BINDIR/golangci-lint
# as a link to it, after checking the archive against the release's SHA256SUMS.
# Platforms: Linux x86-64 and ARM64 (static binaries), macOS on Apple silicon and Intel.
# vgolint reads the standard library and the module cache as golangci-lint does, so Go must be installed
# where it runs, and the modules downloaded (go mod download).
set -eu

repo="vu0tran/vu"
releases="${VGOLINT_RELEASES:-https://github.com/$repo/releases}"
api="${VGOLINT_API:-https://api.github.com/repos/$repo}"
bindir=./bin
debug=0
force=0
alias=1

say() { printf 'vgolint install: %s\n' "$*" >&2; }
log() { [ "$debug" = 1 ] && say "$*"; return 0; }
die() { say "$*"; exit 1; }
usage() {
  cat >&2 <<'EOF'
Usage: install.sh [-b BINDIR] [-d] [-f] [-n] [TAG]
  -b  where to put the binary (default ./bin)
  -d  debug output
  -f  replace a golangci-lint that is already in BINDIR
  -n  install vgolint only, without the golangci-lint name
  TAG a vgolint release: v0.1.0, 0.1.0 or vgolint-v0.1.0 (default: the latest)
EOF
  exit 2
}

while getopts "b:dfnh?x" arg; do
  case "$arg" in
    b) bindir="$OPTARG" ;;
    d) debug=1 ;;
    f) force=1 ;;
    n) alias=0 ;;
    x) set -x ;;
    *) usage ;;
  esac
done
shift $((OPTIND - 1))
tag="${1:-}"

if command -v curl >/dev/null 2>&1; then
  get() { if [ -n "${GITHUB_TOKEN:-}" ] && [ "${1#"$api"}" != "$1" ]; then curl -fsSL --retry 3 -H "Authorization: Bearer $GITHUB_TOKEN" -o "$2" "$1"; else curl -fsSL --retry 3 -o "$2" "$1"; fi; }
elif command -v wget >/dev/null 2>&1; then
  get() { wget -q -O "$2" "$1"; }
else
  die "needs curl or wget"
fi

os=$(uname -s); arch=$(uname -m)
case "$os" in
  Linux) os=linux ;;
  Darwin) os=darwin ;;
  *) die "there's no vgolint release for $os (Linux and macOS only); build it from source: https://github.com/$repo/tree/main/golint" ;;
esac
case "$arch" in
  x86_64 | amd64) arch=amd64 ;;
  aarch64 | arm64) arch=arm64 ;;
  *) die "there's no vgolint release for $arch (amd64 and arm64 only)" ;;
esac
# a shell under Rosetta on Apple silicon says x86_64
if [ "$os/$arch" = darwin/amd64 ] && [ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" = 1 ]; then arch=arm64; fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT INT TERM

if [ -z "$tag" ] || [ "$tag" = latest ]; then
  # the repository's latest release is Vu's own; the newest vgolint-v* one is wanted
  get "$api/releases?per_page=100" "$tmp/releases.json" || die "can't list the releases at $api (set GITHUB_TOKEN if you hit the API's rate limit)"
  tag=$(sed -n 's/.*"tag_name": *"\(vgolint-v[^"]*\)".*/\1/p' "$tmp/releases.json" | head -1)
  [ -n "$tag" ] || die "there's no vgolint release yet at $releases"
fi
v="${tag#vgolint-}"; v="${v#v}"
case "$v" in
  "" | */* | *" "*) die "'$tag' isn't a vgolint version" ;;
esac
tag="vgolint-v$v"
name="vgolint-$v-$os-$arch"
log "installing $tag ($name) into $bindir"

get "$releases/download/$tag/$name.tar.gz" "$tmp/$name.tar.gz" ||
  die "no $name.tar.gz in release $tag (vgolint's versions are its own, not golangci-lint's: see $releases)"
get "$releases/download/$tag/SHA256SUMS" "$tmp/SHA256SUMS" || die "no SHA256SUMS in release $tag"
want=$(awk -v f="$name.tar.gz" '$2 == f || $2 == "*" f { print $1 }' "$tmp/SHA256SUMS")
[ -n "$want" ] || die "$name.tar.gz isn't in the release's SHA256SUMS"
if command -v sha256sum >/dev/null 2>&1; then have=$(sha256sum "$tmp/$name.tar.gz" | awk '{print $1}')
else have=$(shasum -a 256 "$tmp/$name.tar.gz" | awk '{print $1}'); fi
[ "$have" = "$want" ] || die "$name.tar.gz doesn't match its SHA-256 sum (got $have, want $want); nothing was installed"
log "checksum ok: $have"

(cd "$tmp" && tar xzf "$name.tar.gz")
mkdir -p "$bindir"
install -m 755 "$tmp/$name/vgolint" "$bindir/vgolint" 2>/dev/null || { cp "$tmp/$name/vgolint" "$bindir/vgolint" && chmod 755 "$bindir/vgolint"; }
say "installed $bindir/vgolint"
if [ "$alias" = 1 ]; then
  g="$bindir/golangci-lint"
  if [ -e "$g" ] && [ "$(readlink "$g" 2>/dev/null || true)" != vgolint ] && [ "$force" != 1 ]; then
    say "$g is already there (not vgolint's): left alone; -f replaces it, or run vgolint"
  else
    rm -f "$g"
    ln -s vgolint "$g"
    say "installed $g (a link to vgolint)"
  fi
fi
