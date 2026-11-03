#!/bin/sh
# Installs one of the drop-in tools from this repository's GitHub releases, with the original's
# command name as a link to it:
#   curl -fsSL https://raw.githubusercontent.com/vu0tran/vu/main/packaging/tools/install.sh | sh -s -- vsc
#   curl -fsSL https://raw.githubusercontent.com/vu0tran/vu/main/packaging/tools/install.sh | sh -s -- vjq -b /usr/local/bin 0.1.0
#
# Usage: install.sh TOOL [-b BINDIR] [-d] [-f] [-n] [VERSION]
#   TOOL     vsc (installs vsc and shellcheck), vjq (vjq and jq), vknip (vknip and knip) or vlint
#            (vlint and oxlint); vgolint has its own installer, golint/install.sh
#   -b       where to put the commands (default ~/.local/bin)
#   -d       debug output
#   -f       replace a command of the original's name that is already in BINDIR (by default it is
#            left alone)
#   -n       install TOOL only, without the original's name
#   VERSION  a release of the tool: 0.1.0, v0.1.0 or TOOL-v0.1.0 (default: the tool's latest release)
#
# The archive is checked against the release's SHA256SUMS before anything is installed.
# Platforms: Linux x86-64 and ARM64 (static binaries: any distribution, glibc or musl), macOS 12 or
# later on Apple silicon and Intel. vsc's archives are .tar.xz, as ShellCheck's are (needs xz).
# vknip runs node for JavaScript and TypeScript configs, as knip does.
set -eu

repo="vu0tran/vu"
releases="${VU_TOOLS_RELEASES:-https://github.com/$repo/releases}"
api="${VU_TOOLS_API:-https://api.github.com/repos/$repo}"
bindir="${HOME:-.}/.local/bin"
debug=0
force=0
alias=1

say() { printf '%s install: %s\n' "${tool:-tool}" "$*" >&2; }
log() { [ "$debug" = 1 ] && say "$*"; return 0; }
die() { say "$*"; exit 1; }
usage() {
  cat >&2 <<'EOF'
Usage: install.sh TOOL [-b BINDIR] [-d] [-f] [-n] [VERSION]
  TOOL  vsc (shellcheck), vjq (jq), vknip (knip) or vlint (oxlint)
  -b    where to put the commands (default ~/.local/bin)
  -d    debug output
  -f    replace a command of the original's name already in BINDIR
  -n    install TOOL only, without the original's name
  VERSION  0.1.0, v0.1.0 or TOOL-v0.1.0 (default: the latest release of TOOL)
EOF
  exit 2
}

tool="${1:-}"
[ -n "$tool" ] || usage
shift
case "$tool" in
  vsc) orig=shellcheck ;;
  vjq) orig=jq ;;
  vknip) orig=knip ;;
  vlint) orig=oxlint ;;
  vgolint) die "vgolint has its own installer, with golangci-lint's interface: https://github.com/$repo/tree/main/golint#install" ;;
  -h | --help) usage ;;
  *) tool=""; die "unknown tool (vsc, vjq, vknip, vlint)" ;;
esac

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
  *) die "there's no $tool release for $os (Linux and macOS only); build it from source: https://github.com/$repo" ;;
esac
case "$arch" in
  x86_64 | amd64) arch=x64 ;;
  aarch64 | arm64) arch=arm64 ;;
  *) die "there's no $tool release for $arch (x86-64 and ARM64 only)" ;;
esac
# a shell under Rosetta on Apple silicon says x86_64
if [ "$os/$arch" = darwin/x64 ] && [ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" = 1 ]; then arch=arm64; fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT INT TERM

if [ -z "$tag" ] || [ "$tag" = latest ]; then
  # the repository's latest release is Vu's own; the newest TOOL-v* one is wanted
  get "$api/releases?per_page=100" "$tmp/releases.json" || die "can't list the releases at $api (set GITHUB_TOKEN if you hit the API's rate limit)"
  tag=$(sed -n "s/.*\"tag_name\": *\"\\($tool-v[^\"]*\\)\".*/\\1/p" "$tmp/releases.json" | head -1)
  [ -n "$tag" ] || die "there's no $tool release yet at $releases"
fi
v="${tag#"$tool"-}"; v="${v#v}"
case "$v" in
  "" | */* | *" "*) die "'$tag' isn't a $tool version" ;;
esac
tag="$tool-v$v"

# the archive's name, as build.sh makes it (the originals' naming schemes), and its folder's
case "$tool" in
  vsc)
    case "$arch" in x64) a=x86_64 ;; *) a=aarch64 ;; esac
    name="vsc-v$v"; file="$name.$os.$a.tar.xz" ;;
  vjq)
    o=$os; [ "$os" = darwin ] && o=macos
    case "$arch" in x64) a=amd64 ;; *) a=arm64 ;; esac
    name="vjq-$v-$o-$a"; file="$name.tar.gz" ;;
  *) name="$tool-$v-$os-$arch"; file="$name.tar.gz" ;;
esac
log "installing $tag ($file) into $bindir"

get "$releases/download/$tag/$file" "$tmp/$file" ||
  die "no $file in release $tag ($tool's versions are its own, not $orig's: see $releases)"
get "$releases/download/$tag/SHA256SUMS" "$tmp/SHA256SUMS" || die "no SHA256SUMS in release $tag"
want=$(awk -v f="$file" '$2 == f || $2 == "*" f { print $1 }' "$tmp/SHA256SUMS")
[ -n "$want" ] || die "$file isn't in the release's SHA256SUMS"
if command -v sha256sum >/dev/null 2>&1; then have=$(sha256sum "$tmp/$file" | awk '{print $1}')
else have=$(shasum -a 256 "$tmp/$file" | awk '{print $1}'); fi
[ "$have" = "$want" ] || die "$file doesn't match its SHA-256 sum (got $have, want $want); nothing was installed"
log "checksum ok: $have"

case "$file" in
  *.tar.xz)
    if ! (cd "$tmp" && tar xJf "$file") 2>/dev/null; then
      command -v xz >/dev/null 2>&1 || die "$file is xz-compressed: install xz (xz-utils) first"
      (cd "$tmp" && xz -dc "$file" | tar xf -)
    fi ;;
  *) (cd "$tmp" && tar xzf "$file") ;;
esac
mkdir -p "$bindir"
install -m 755 "$tmp/$name/$tool" "$bindir/$tool" 2>/dev/null || { cp "$tmp/$name/$tool" "$bindir/$tool" && chmod 755 "$bindir/$tool"; }
say "installed $bindir/$tool"
if [ "$alias" = 1 ]; then
  g="$bindir/$orig"
  if [ -e "$g" ] && [ "$(readlink "$g" 2>/dev/null || true)" != "$tool" ] && [ "$force" != 1 ]; then
    say "$g is already there (not $tool's): left alone; -f replaces it, or run $tool"
  else
    rm -f "$g"
    ln -s "$tool" "$g"
    say "installed $g (a link to $tool)"
  fi
fi
case ":${PATH:-}:" in
  *":$bindir:"*) ;;
  *) say "$bindir isn't on PATH: add it (export PATH=\"$bindir:\$PATH\")" ;;
esac
