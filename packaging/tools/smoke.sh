#!/bin/sh
# Runs a released binary on a small fixture and compares what it prints with what the original
# tool prints there (saved from oxlint 1.90.0 and golangci-lint 2.5.0):
#   packaging/tools/smoke.sh vlint PATH/TO/vlint
#   packaging/tools/smoke.sh vgolint PATH/TO/vgolint      (needs Go: the standard library's source)
set -eu
tool="$1"; bin="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
here="$(cd "$(dirname "$0")" && pwd)"
fx="$here/fixtures"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT INT TERM
fail() { echo "smoke: $tool: $*" >&2; exit 1; }
case "$tool" in
  vlint)
    cp -R "$fx/vlint" "$tmp/p"
    cd "$tmp/p"
    # named files, then no paths (the current folder, as oxlint does); oxlint's order isn't fixed
    "$bin" a.ts b.jsx > "$tmp/out1" || fail "exit code $? on named files"
    sort "$tmp/out1" | diff "$fx/vlint.expected" - || fail "output differs (named files)"
    "$bin" > "$tmp/out2" || fail "exit code $? with no paths"
    sort "$tmp/out2" | diff "$fx/vlint.expected" - || fail "output differs (no paths)"
    # (an option it doesn't have is refused, not read as a path)
    if "$bin" --deny-warnings >/dev/null 2>&1; then fail "accepted an unknown option"; fi
    ;;
  vgolint)
    cp -R "$fx/vgolint" "$tmp/m"
    cd "$tmp/m"
    set +e
    "$bin" run --no-cache > "$tmp/out" 2> "$tmp/err"
    rc=$?
    set -e
    diff "$fx/vgolint.expected" "$tmp/out" || { cat "$tmp/err" >&2; fail "output differs"; }
    [ "$rc" = 1 ] || { cat "$tmp/err" >&2; fail "exit code $rc, want 1 (issues found)"; }
    "$bin" version | grep -q '^golangci-lint has version 2\.5\.0 built with vgolint' || fail "version: $("$bin" version)"
    ;;
  *) fail "unknown tool" ;;
esac
echo "smoke: $tool: ok ($bin)"
