#!/bin/sh
# Runs a released binary on a small fixture and compares what it prints with what the original
# tool prints there (saved from oxlint 1.90.0, golangci-lint 2.5.0, ShellCheck 0.11.0, jq 1.7.1 and
# knip 6.44.1):
#   packaging/tools/smoke.sh vlint PATH/TO/vlint
#   packaging/tools/smoke.sh vgolint PATH/TO/vgolint      (needs Go: the standard library's source)
#   packaging/tools/smoke.sh vsc PATH/TO/vsc              (run as shellcheck)
#   packaging/tools/smoke.sh vjq PATH/TO/vjq              (run as jq)
#   packaging/tools/smoke.sh vknip PATH/TO/vknip          (run as knip; needs node, for knip.config.ts)
# PATH can also be the original's command name (shellcheck, jq, knip: npm's launcher, say).
# For vsc, vjq and vknip, the fixture's commands and their stdout, stderr and exit codes go in one
# transcript, compared with fixtures/TOOL.expected; SMOKE_SAVE=1 with the original tool as PATH
# (shellcheck 0.11.0, jq 1.7.1, knip 6.44.1's bin/knip.js) writes that file instead.
set -eu
tool="$1"; bin="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
[ -x "$bin" ] || { echo "smoke: $tool: no program $bin" >&2; exit 1; }
here="$(cd "$(dirname "$0")" && pwd)"
fx="$here/fixtures"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT INT TERM
fail() { echo "smoke: $tool: $*" >&2; exit 1; }
# t CMD ARGS...: runs a command, appends it and what it printed to the transcript
t() {
  printf '== %s\n' "$*" >> "$tmp/got"
  set +e
  "$@" > "$tmp/o" 2> "$tmp/e"
  rc=$?
  set -e
  cat "$tmp/o" >> "$tmp/got"
  if [ -s "$tmp/e" ]; then printf -- '-- stderr\n' >> "$tmp/got"; cat "$tmp/e" >> "$tmp/got"; fi
  printf -- '-- exit %s\n' "$rc" >> "$tmp/got"
}
# the binary under the original's name, first on PATH (jq's and ShellCheck's messages name argv[0])
as() {
  mkdir -p "$tmp/bin"
  ln -sf "$bin" "$tmp/bin/$1"
  PATH="$tmp/bin:$PATH"
  export PATH
}
transcript() {
  if [ "${SMOKE_SAVE:-}" = 1 ]; then cp "$tmp/got" "$fx/$tool.expected"; echo "smoke: wrote $fx/$tool.expected"; exit 0; fi
  diff "$fx/$tool.expected" "$tmp/got" || fail "output differs from the original's (above: < original, > $bin)"
}
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
  vsc)
    cp -R "$fx/vsc" "$tmp/p"
    as shellcheck
    cd "$tmp/p"
    t shellcheck deploy.sh lib.bash clean.sh
    t shellcheck -f gcc deploy.sh lib.bash clean.sh
    t shellcheck -f json1 -S warning deploy.sh lib.bash
    t shellcheck -f diff deploy.sh
    t shellcheck -f checkstyle -e SC2086 lib.bash
    t shellcheck -s bash -o all clean.sh
    t shellcheck -s bash - < deploy.sh
    t shellcheck clean.sh missing.sh
    t shellcheck --format=xml clean.sh
    t shellcheck --version
    transcript
    ;;
  vjq)
    cp -R "$fx/vjq" "$tmp/p"
    as jq
    cd "$tmp/p"
    while IFS= read -r f; do t jq -c "$f" users.json; done < filters.txt
    t jq .meta users.json
    t jq --tab -S .users[2] users.json
    t jq -r '.users[] | [.name, .age] | @tsv' users.json
    VJQ_SMOKE=yes; export VJQ_SMOKE
    # shellcheck disable=SC2016
    t jq -nr --arg a 1 --argjson b '{"x":[2]}' '"\($a) \($b.x[0])", $ENV.VJQ_SMOKE, ([$a, $b.x[0]] | @csv)'
    t jq -e '.users[5]' users.json
    t jq -s 'map(.meta.count)' users.json users.json
    t jq --unknown-option .
    t jq . missing.json
    t jq --version
    transcript
    ;;
  vknip)
    cp -R "$fx/vknip" "$tmp/p"
    as knip
    cd "$tmp/p"
    t knip
    t knip --reporter compact
    t knip --reporter json
    t knip --include files,exports --no-exit-code
    t knip --production
    t knip --no-such-option
    t knip --version
    transcript
    ;;
  *) fail "unknown tool" ;;
esac
echo "smoke: $tool: ok ($bin)"
