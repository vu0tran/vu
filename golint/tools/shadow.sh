#!/bin/sh
# shadow.sh [ARGS...]: vgolint beside golangci-lint, for trying vgolint in CI before switching.
#
# Runs `golangci-lint run ARGS` (its exit code is this script's: it stays the check that blocks), then
# both tools again with the limits that make golangci-lint's output depend on its run order turned off
# (--max-issues-per-linter 0 --max-same-issues 0 --uniq-by-line=false), and compares the issues they
# report, one line each, sorted. Differences are printed and, with SHADOW_REPORT=FILE, written there;
# they don't fail the job unless SHADOW_STRICT=1. A vgolint crash or error (an exit code other than 0
# or the issues exit code) is reported the same way.
#
#   GOLANGCI_LINT (default: golangci-lint), VGOLINT (default: vgolint)
set -u
gl=${GOLANGCI_LINT:-golangci-lint}
vg=${VGOLINT:-vgolint}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

"$gl" run "$@"
rc=$?

lim="--max-issues-per-linter 0 --max-same-issues 0 --uniq-by-line=false --output.text.print-issued-lines=false"
# (golangci-lint's own cache doesn't notice every settings change: a fresh one for the comparison)
GOLANGCI_LINT_CACHE="$tmp/gcache" "$gl" run $lim "$@" > "$tmp/gl.out" 2> "$tmp/gl.err"
glrc=$?
"$vg" run $lim "$@" > "$tmp/vg.out" 2> "$tmp/vg.err"
vgrc=$?

issues() { grep -E '^[^ 	].*:[0-9]+(:[0-9]+)?: ' "$1" | sort; }
issues "$tmp/gl.out" > "$tmp/gl.iss"
issues "$tmp/vg.out" > "$tmp/vg.iss"

report=${SHADOW_REPORT:-$tmp/report}
{
  if [ $vgrc -ne 0 ] && [ $vgrc -ne $glrc ] && [ $vgrc -ne 1 ]; then
    echo "vgolint exited with $vgrc (golangci-lint $glrc):"; tail -20 "$tmp/vg.err"
  fi
  if ! cmp -s "$tmp/gl.iss" "$tmp/vg.iss"; then
    echo "issues only golangci-lint reports: $(comm -23 "$tmp/gl.iss" "$tmp/vg.iss" | wc -l | tr -d ' ')"
    comm -23 "$tmp/gl.iss" "$tmp/vg.iss" | head -50
    echo "issues only vgolint reports: $(comm -13 "$tmp/gl.iss" "$tmp/vg.iss" | wc -l | tr -d ' ')"
    comm -13 "$tmp/gl.iss" "$tmp/vg.iss" | head -50
  fi
  grep 'not implemented yet' "$tmp/vg.err"
} > "$report"

if [ -s "$report" ]; then
  echo "shadow: vgolint differs from golangci-lint:"; cat "$report"
  [ "${SHADOW_STRICT:-0}" = 1 ] && [ $rc -eq 0 ] && rc=1
else
  echo "shadow: vgolint reports the same $(wc -l < "$tmp/gl.iss" | tr -d ' ') issues as golangci-lint"
fi
exit $rc
