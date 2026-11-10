#!/bin/bash
# oxprobe.sh [-n N] [--save] [--vlint PATH] DIR... [-- ARGS]
#
# Runs oxlint and vlint on each probe folder (with ARGS, default none; e.g. -- -A all -D no-empty)
# and prints only the differences, grouped by rule and capped at N lines a group (default 15).
# One summary line a folder: "DIR: same (K diagnostics)" or "DIR: D differ (oxlint-only A,
# vlint-only B)".
#
# oxlint is $OXLINT (else `oxlint` on PATH). Without oxlint, or with --saved, a folder's saved
# expected output (DIR/.oxlint.txt) is used instead; --save writes it from oxlint. The folders in
# ts/probes/ are kept with their saved output, so `./oxprobe.sh probes/*` is a quick regression
# check that needs no oxlint.
#
# Both run in the folder with --format unix, so its own config (if any) applies to both.
set -u
here=$(cd "$(dirname "$0")" && pwd)
N=15
save=0
saved=0
VL="$here/vlint"
dirs=()
while [ $# -gt 0 ]; do
  case "$1" in
    -n) N=$2; shift 2 ;;
    --save) save=1; shift ;;
    --saved) saved=1; shift ;;
    --vlint) VL=$(readlink -f "$2"); shift 2 ;;
    --) shift; break ;;
    *) dirs+=("$1"); shift ;;
  esac
done
args=("$@")
OX=${OXLINT:-$(command -v oxlint || true)}
[ -x "$VL" ] || { echo "oxprobe: no vlint at $VL (build it, or pass --vlint)" >&2; exit 2; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
# (the summary line "N problems" and blank lines are dropped; the rest sorted)
norm() { grep -v -e '^$' -e '^[0-9]* problems\?$' -e '^Found [0-9]' | sort; }
bad=0
for d in "${dirs[@]}"; do
  [ -d "$d" ] || { echo "$d: not a folder"; bad=1; continue; }
  exp="$d/.oxlint.txt"
  if [ $saved -eq 0 ] && [ -n "$OX" ]; then
    (cd "$d" && "$OX" --format unix "${args[@]}" . 2>&1) | norm > "$tmp/o"
    [ $save -eq 1 ] && cp "$tmp/o" "$exp"
  elif [ -f "$exp" ]; then
    cp "$exp" "$tmp/o"
  else
    echo "$d: no oxlint (set OXLINT) and no saved $exp"; bad=1; continue
  fi
  (cd "$d" && "$VL" --format unix "${args[@]}" . 2>&1) | norm > "$tmp/v"
  comm -23 "$tmp/o" "$tmp/v" > "$tmp/oo"
  comm -13 "$tmp/o" "$tmp/v" > "$tmp/vo"
  a=$(wc -l < "$tmp/oo"); b=$(wc -l < "$tmp/vo")
  if [ "$a" -eq 0 ] && [ "$b" -eq 0 ]; then
    echo "$d: same ($(wc -l < "$tmp/o") diagnostics)"
    continue
  fi
  bad=1
  echo "$d: $((a + b)) differ (oxlint-only $a, vlint-only $b)"
  # group by the rule in [...] at the end ("parse" for errors without one), oxlint's side first
  python3 -I - "$tmp/oo" "$tmp/vo" "$N" <<'EOF'
import re, sys
oo, vo, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
groups = {}
for side, f in (("O", oo), ("V", vo)):
    for line in open(f, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        m = re.search(r"\[(?:Warning|Error)/([^\]]+)\]$", line)
        rule = m.group(1) if m else ("error" if "[Error]" in line else "other")
        groups.setdefault(rule, []).append(side + " " + line)
for rule in sorted(groups, key=lambda r: -len(groups[r])):
    xs = groups[rule]
    print(f"  {rule}: {len(xs)}")
    for x in xs[:n]:
        print("    " + x[:220])
    if len(xs) > n:
        print(f"    ... {len(xs) - n} more")
EOF
done
exit $bad
