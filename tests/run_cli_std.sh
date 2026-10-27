#!/bin/bash
# std/cli: tests/cli/serve.vu given many command lines; what it prints, or the error it stops with.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
$VU build cli/serve.vu -o "$work/serve" $1 >/dev/null || { echo "FAIL  build"; exit 1; }
$VU build cli/dup.vu -o "$work/dup" $1 >/dev/null || { echo "FAIL  build"; exit 1; }
pass=0; fail=0
t() {  # expected (substring of the output, stdout and stderr together), arguments...
  local want=$1; shift
  local got; got=$("$work/serve" "$@" 2>&1)
  if printf '%s' "$got" | grep -qF -- "$want" && ! printf '%s' "$got" | grep -q 'ERROR\|runtime error'; then pass=$((pass+1))
  else fail=$((fail+1)); echo "FAIL  serve $*"; echo "      want: $want"; echo "      got:  $(printf '%s' "$got" | head -3)"; fi
}
t "verbose=false quiet=false port=8080 root=/srv mode=dev headers= files=" -r /srv dev
t "verbose=true quiet=true port=9 root=/x mode=dev headers=a:1,b:2 files=a,b,-notflag" dev a b --root=/x -vq --port 9 -H a:1 -Hb:2 -- -notflag
t "port=7 root=/r" -vp7 -r/r m
t "port=3" -p 1 --port=2 -p3 -r x m
t "port=" --port= -r x m
t "root=--weird" --root --weird m
t "mode=- " -r x -
t "files=x,-y" -r x m -- x -y
t "usage: serve [options] --root ROOT mode [files...]" --help
t "usage: serve" -vh
t "  -p, --port PORT      the port to listen on (default: 8080)" -h
t "serve: unknown option '--nope'" --nope -r x m
t "serve: unknown option '-z'" -vz -r x m
t "serve: --port needs a value" -r x m --port
t "serve: -p (--port) needs a value" -r x m -p
t "serve: --verbose is a flag: it takes no value" --verbose=yes -r x m
t "serve: missing mode" -r x
t "serve: --root must be given" m
t "Serves a folder over HTTP." m
got=$("$work/dup" 2>&1)
if printf '%s' "$got" | grep -qF "cli: two arguments are named 'port'"; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL  dup: $got"; fi
# random command lines: each one parses or fails with a message, never anything else
r=$(python3 - "$work/serve" <<'PY'
import random, subprocess, sys
rng = random.Random(3)
toks = ['-v', '-q', '-vq', '-p', '-p9', '--port', '--port=', '--port=1', '-H', '-Hx', '--header=a', '-r', '--root', '--root=/', '--',
        '-', '--nope', '-z', '-h', '--help', 'm', 'x', 'é', '-ve', '--=', '---', '-', '', ' ', '--verbose=1', '-rp']
bad = 0
for i in range(400):
    argv = [rng.choice(toks) for _ in range(rng.randint(0, 7))]
    r = subprocess.run([sys.argv[1]] + argv, capture_output=True, text=True, timeout=30)
    ok = (r.returncode == 0 and (r.stdout.startswith('verbose=') or r.stdout.startswith('usage:'))) or (r.returncode == 1 and r.stderr.startswith('error: serve: '))
    if not ok or 'ERROR' in r.stderr or 'runtime error' in r.stderr:
        bad += 1
        if bad < 4: print('bad', argv, r.returncode, r.stdout[:100], r.stderr[:200])
print('random', bad)
PY
)
if [ "$(echo "$r" | tail -1)" = "random 0" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL  random command lines: $r"; fi
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
