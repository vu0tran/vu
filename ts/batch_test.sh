#!/bin/bash
# batch_test.sh VLINT: vlint --batch against the same runs one at a time. A monorepo made in a
# temporary directory: packages with their own configurations, a local JS plugin with options that
# differ by package, two copies of one plugin under the same name, a deferred native plugin's alias
# taken by a package, a broken configuration, a path with no files, and an unknown flag. Each run's
# stdout, stderr and exit code must be what it is alone, at 1, 2 and 6 runs at a time, in the
# plan's order and by size, and with the batch's sharing off. Prints one line a case and
# "batch: N failed".
set -u
VL=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
export XDG_CACHE_HOME=$tmp/xdg VLINT_VTSC_CACHE=0 LC_ALL=C
unset VLINT_BATCH_JOBS VLINT_BATCH_ORDER VLINT_BATCH_CAP VLINT_BATCH_SHARE VTSC_PKG_TREES
R=$tmp/repo
mkdir -p "$R"
cd "$R" || exit 1
git init -q .

# a JS plugin: one rule reporting each `debugger`-free function's name when it matches the option
plugin() {
  mkdir -p "$1"
  cat > "$1/package.json" <<EOF
{"name": "$2", "version": "1.0.0", "main": "index.js"}
EOF
  cat > "$1/index.js" <<EOF
const name = {
  meta: { type: "problem", schema: [{ type: "string" }] },
  create(context) {
    const want = context.options[0] || "bad";
    return { FunctionDeclaration(n) { if (n.id && n.id.name.includes(want)) context.report({ node: n.id, message: "$3 " + want + ": " + n.id.name }); } };
  },
};
const count = { meta: { type: "problem" }, create(context) { return { "Program:exit"(n) { if (n.body.length > 3) context.report({ node: n, message: "$3 long file" }); } }; } };
module.exports = { meta: { name: "$2" }, rules: { name, count } };
EOF
}
plugin node_modules/eslint-plugin-local eslint-plugin-local local
# (a second copy, under the same alias in another package: the batch's host already knows the name)
plugin pkgs/d/node_modules/eslint-plugin-local eslint-plugin-local copy

pkg() {
  local d=pkgs/$1
  mkdir -p "$d/src"
  for k in 1 2 3; do
    cat > "$d/src/f$k.ts" <<EOF
export function ${1}bad$k(x: number) { debugger; return x + $k; }
export function ${1}ok$k() { var unused = 1; return 2; }
export const v$k = 1 == 1;
export function ${1}zz$k() { return 3; }
EOF
  done
  cat > "$d/.oxlintrc.json"
}
pkg a <<'EOF'
{"jsPlugins": ["eslint-plugin-local"], "rules": {"local/name": ["error", "bad"], "local/count": "warn", "no-debugger": "error", "eqeqeq": "error"}}
EOF
pkg b <<'EOF'
{"jsPlugins": ["eslint-plugin-local"], "rules": {"local/name": ["error", "ok"], "no-debugger": "off", "no-unused-vars": "error"}}
EOF
pkg c <<'EOF'
{"rules": {"no-debugger": "warn", "eqeqeq": "error"}}
EOF
pkg d <<'EOF'
{"jsPlugins": [{"name": "local", "specifier": "eslint-plugin-local"}], "rules": {"local/name": ["error", "zz"], "local/count": "error"}}
EOF
pkg e <<'EOF'
{"jsPlugins": ["eslint-plugin-local"], "rules": {"local/name": ["error", "bad"], "local/nope": "error"}}
EOF
pkg f <<'EOF'
{ "rules": { "no-debugger": "error", }
EOF
pkg g <<'EOF'
{"jsPlugins": ["eslint-plugin-local"], "rules": {"local/name": ["warn", "zz"], "local/count": "error"}, "overrides": [{"files": ["src/f2.ts"], "rules": {"local/name": ["error", "ok"]}}]}
EOF

# the runs: [args...] per line
runs=(
  "-c pkgs/a/.oxlintrc.json pkgs/a/src"
  "-c pkgs/b/.oxlintrc.json --format unix pkgs/b/src"
  "-c pkgs/c/.oxlintrc.json --format json pkgs/c/src"
  "-c pkgs/d/.oxlintrc.json --format unix pkgs/d/src"
  "-c pkgs/e/.oxlintrc.json pkgs/e/src"
  "-c pkgs/f/.oxlintrc.json pkgs/f/src"
  "-c pkgs/g/.oxlintrc.json --format unix -D warnings pkgs/g/src"
  "-c pkgs/a/.oxlintrc.json pkgs/nothing"
  "-c pkgs/a/.oxlintrc.json --no-error-on-unmatched-pattern pkgs/nothing"
  "--bogus-flag pkgs/a/src"
  "-c pkgs/b/.oxlintrc.json --format unix --max-warnings 0 pkgs/b/src pkgs/g/src"
  "-c pkgs/a/.oxlintrc.json --format unix pkgs/a/src/f1.ts"
)
# (the run alone: its outputs, with the timing line's milliseconds dropped)
clean() { sed -E 's/in [0-9.]+(ms|s) on/in T on/; s/"start_time": [0-9.e-]+/"start_time": T/' "$1"; }
mkdir -p "$tmp/alone"
for i in "${!runs[@]}"; do
  # shellcheck disable=SC2086
  "$VL" ${runs[$i]} > "$tmp/alone/$i.out" 2> "$tmp/alone/$i.err"
  echo $? > "$tmp/alone/$i.exit"
done
fails=0
# (the runs alone must say something: the plugins' reports, both copies', and the errors)
for want in "local bad: abad1" "copy zz: dzz1" "local ok: bok1" "local long file" "Failed to parse oxlint configuration file" "not expected in this context" "No files found to lint" "local zz: gzz3"; do
  if ! cat "$tmp"/alone/*.out "$tmp"/alone/*.err | grep -q "$want"; then echo "FAIL alone: no \"$want\""; fails=$((fails + 1)); fi
done
check() {
  local tag=$1
  shift
  local d=$tmp/b_$tag
  mkdir -p "$d"
  {
    echo "["
    for i in "${!runs[@]}"; do
      local sep=","
      [ "$i" -eq $((${#runs[@]} - 1)) ] && sep=""
      printf '{"args": [%s], "out": "%s/%s.out", "err": "%s/%s.err", "exit": "%s/%s.exit"}%s\n' "$(printf '"%s",' ${runs[$i]} | sed 's/,$//')" "$d" "$i" "$d" "$i" "$d" "$i" "$sep"
    done
    echo "]"
  } > "$d/plan.json"
  env "$@" "$VL" --batch "$d/plan.json" > "$d/batch.out" 2> "$d/batch.err"
  local rc=$? worst=0 bad=""
  for i in "${!runs[@]}"; do
    local x
    x=$(cat "$tmp/alone/$i.exit")
    [ "$x" -gt "$worst" ] && worst=$x
    for k in out err exit; do
      if [ "$k" = exit ]; then cmp -s "$tmp/alone/$i.$k" "$d/$i.$k" || bad="$bad $i.$k"
      else cmp -s <(clean "$tmp/alone/$i.$k") <(clean "$d/$i.$k") || bad="$bad $i.$k"; fi
    done
  done
  [ "$rc" -eq "$worst" ] || bad="$bad exit($rc, not $worst)"
  [ -s "$d/batch.out" ] && bad="$bad batch-stdout"
  [ -s "$d/batch.err" ] && bad="$bad batch-stderr"
  if [ -z "$bad" ]; then echo "ok   $tag"
  else
    echo "FAIL $tag:$bad"
    fails=$((fails + 1))
    for b in $bad; do
      case "$b" in *.out|*.err) diff <(clean "$tmp/alone/$b") <(clean "$d/$b") | head -5 ;; esac
    done
  fi
}
check jobs1 VLINT_BATCH_JOBS=1
check jobs2 VLINT_BATCH_JOBS=2
check jobs6 VLINT_BATCH_JOBS=6
check plan-order VLINT_BATCH_ORDER=plan VLINT_BATCH_JOBS=6
check no-share VLINT_BATCH_SHARE=0 VLINT_BATCH_JOBS=6
check cap VLINT_BATCH_CAP=1 VLINT_BATCH_JOBS=6

# a plan the batch can't read: its usage error, exit 2
echo '{"args": []}' > "$tmp/badplan.json"
"$VL" --batch "$tmp/badplan.json" > /dev/null 2> "$tmp/bp.err"
rc=$?
if [ "$rc" -eq 2 ] && grep -q "not a JSON array" "$tmp/bp.err"; then echo "ok   bad-plan"
else echo "FAIL bad-plan: exit $rc, $(cat "$tmp/bp.err")"; fails=$((fails + 1)); fi
# a run without out/err/exit: printed by the batch, in the plan's order
printf '[{"args": ["-c", "pkgs/c/.oxlintrc.json", "--format", "unix", "pkgs/c/src"]}, {"args": ["-c", "pkgs/a/.oxlintrc.json", "--format", "unix", "pkgs/a/src"]}]\n' > "$tmp/pp.json"
VLINT_BATCH_JOBS=2 "$VL" --batch "$tmp/pp.json" > "$tmp/pp.out" 2> /dev/null
{ "$VL" -c pkgs/c/.oxlintrc.json --format unix pkgs/c/src; "$VL" -c pkgs/a/.oxlintrc.json --format unix pkgs/a/src; } > "$tmp/pp.want" 2> /dev/null
if cmp -s <(clean "$tmp/pp.out") <(clean "$tmp/pp.want"); then echo "ok   printed"
else echo "FAIL printed"; diff <(clean "$tmp/pp.want") <(clean "$tmp/pp.out") | head -5; fails=$((fails + 1)); fi
echo "batch: $fails failed"
[ "$fails" -eq 0 ]
