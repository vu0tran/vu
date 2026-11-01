#!/bin/sh
# vu speedup: each port in examples/speedup and tests/speedup checked against its Python on generated
# inputs; the model loop against a fake Anthropic API (a port that doesn't compile, one with wrong
# answers, then the right one); the swap and running it again; a function the Vu version isn't faster
# at, left alone; refusals (a function that changes its arguments, a wrong hint); exceptions of the
# module's own class; threads with panics in between; surrogates, NUL and bools going to the original;
# agent mode without a key; the ctypes loader (no Python headers); and Float methods against Python's
# math module, last bit included (all but hypot: Python's math.hypot is its own algorithm, not C's).
#   tests/run_speedup.sh
d="$(cd "$(dirname "$0")" && pwd)"
top="$d/.."
VU="$top/vu"
PY=${SPEEDUP_PY:-python3}
work=$(mktemp -d)
trap 'kill $fake 2>/dev/null; rm -rf "$work"' EXIT
pass=0; fail=0
ok() { pass=$((pass+1)); echo "ok    $1"; }
bad() { fail=$((fail+1)); echo "FAIL  $1"; [ -n "$2" ] && printf '%s\n' "$2" | head -30 | sed 's/^/      /'; }
"$VU" version >/dev/null || exit 1

# the ports: same answers on every input
for c in "closematch suggest close_matches" "names names jaro_winkler_similarity" "names names damerau_levenshtein_distance" \
         "names names closest_names" "geo geo track_km" "geo geo nearest" "demo typos did_you_mean"; do
  set -- $c
  rm -rf "$work/$1"; cp -r "$top/examples/speedup/$1" "$work/$1"; rm -rf "$work/$1/_vu_$2"
  out=$(cd "$work/$1" && PYTHON=$PY "$VU" speedup "$2.py:$3" --port "$3.vu" --no-apply --inputs 2000 2>&1)
  if printf '%s' "$out" | grep -q "^same answers as the original on all"; then ok "$3: $(printf '%s' "$out" | grep '^same answers' | cut -c1-80)"
  else bad "$3" "$out"; fi
done

# the ctypes loader, for machines without Python's headers
rm -rf "$work/ct"; cp -r "$top/examples/speedup/names" "$work/ct"; rm -rf "$work/ct/_vu_names"
out=$(cd "$work/ct" && VU_SPEEDUP_CTYPES=1 PYTHON=$PY "$VU" speedup names.py:closest_names --port closest_names.vu --no-apply --inputs 1500 2>&1)
if printf '%s' "$out" | grep -q "^same answers" && [ -z "$(ls "$work/ct/_vu_names" | grep _vu_ext_)" ]; then ok "the ctypes loader (no extension built)"
else bad "the ctypes loader" "$out"; fi

# the model loop: a port that doesn't compile, one with wrong answers, the right one
m="$work/model"; mkdir -p "$m/req"; cp "$top/examples/speedup/closematch/suggest.py" "$m/"
P="$top/examples/speedup/closematch/close_matches.vu"
sed 's/p.x > q.x/p.x < q.x/' "$P" > "$m/wrong.vu"; sed 's/word.codes()/word.codez()/' "$P" > "$m/broken.vu"
$PY "$d/speedup/fake_model.py" "$m/port" "$m/req" "$m/broken.vu" "$m/wrong.vu" "$P" & fake=$!
i=0; while [ ! -s "$m/port" ] && [ $i -lt 600 ]; do sleep 0.1; i=$((i+1)); done
out=$(cd "$m" && ANTHROPIC_API_KEY=test-key ANTHROPIC_BASE_URL="http://127.0.0.1:$(cat "$m/port")" PYTHON=$PY "$VU" speedup suggest.py:close_matches --no-apply --inputs 1500 2>&1)
kill $fake 2>/dev/null
fb1=$($PY -c "import json,sys; m=json.load(open(sys.argv[1]))['body']['messages']; print(m[-1]['content'][:200])" "$m/req/1.json" 2>&1)
fb2=$($PY -c "import json,sys; m=json.load(open(sys.argv[1]))['body']['messages']; print(m[-1]['content'][:200])" "$m/req/2.json" 2>&1)
key=$($PY -c "import json,sys; print(json.load(open(sys.argv[1]))['key'])" "$m/req/0.json" 2>&1)
llms=$($PY -c "import json,sys; print('<vu>' in json.load(open(sys.argv[1]))['body']['messages'][0]['content'])" "$m/req/0.json" 2>&1)
if printf '%s' "$out" | grep -q "attempt 3" && printf '%s' "$out" | grep -q "^same answers" && printf '%s' "$fb1" | grep -q "doesn't compile" \
   && printf '%s' "$fb2" | grep -q "answers differ" && [ "$key" = test-key ] && [ "$llms" = True ]; then
  ok "the model loop: compile errors and wrong answers fed back, the third port accepted"
else bad "the model loop" "$out
$fb1
$fb2
key $key llms $llms"; fi

# a model API it can't reach: one line saying so, no traceback
out=$(cd "$m" && ANTHROPIC_API_KEY=test-key ANTHROPIC_BASE_URL="http://127.0.0.1:1" PYTHON=$PY "$VU" speedup suggest.py:close_matches --no-apply --inputs 200 2>&1); rc=$?
if [ $rc -ne 0 ] && printf '%s' "$out" | grep -q "can't reach the model API" && ! printf '%s' "$out" | grep -q Traceback; then
  ok "a model API it can't reach: said in one line"
else bad "an unreachable model API" "$out"; fi

# agent mode: no key, no port: the prompt is written, exit 2
rm -rf "$work/agent"; mkdir "$work/agent"; cp "$top/examples/speedup/closematch/suggest.py" "$work/agent/"
out=$(cd "$work/agent" && env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY PYTHON=$PY "$VU" speedup suggest.py:close_matches 2>&1); rc=$?
if [ $rc -eq 2 ] && grep -q "class SequenceMatcher" "$work/agent/_vu_suggest/close_matches.prompt.md" \
   && grep -q "fn close_matches(word: Str, possibilities: \[Str\], n: Int, cutoff: Float) -> \[Str\]" "$work/agent/_vu_suggest/close_matches.prompt.md"; then
  ok "agent mode: the prompt (with difflib's source and the Vu signature) written, exit 2"
else bad "agent mode (exit $rc)" "$out"; fi

# the swap, the module using it, and a second run that doesn't add it again
s="$work/swap"; rm -rf "$s"; cp -r "$top/examples/speedup/closematch" "$s"; rm -rf "$s/_vu_suggest"
out=$(cd "$s" && PYTHON=$PY "$VU" speedup suggest.py:close_matches --port close_matches.vu --inputs 1500 2>&1)
use=$(cd "$s" && $PY -c "
import suggest, difflib
f = suggest.close_matches
print(hasattr(f, '__vu_original__'), f('appel', ['ape', 'apple', 'peach', 'puppy']) == difflib.get_close_matches('appel', ['ape', 'apple', 'peach', 'puppy']), f('x', ['x'], 2**70) == ['x'])" 2>&1)
out2=$(cd "$s" && PYTHON=$PY "$VU" speedup suggest.py:close_matches --port close_matches.vu --inputs 500 2>&1)
if [ "$use" = "True True True" ] && [ "$(grep -c '^# vu speedup:' "$s/suggest.py")" = 1 ] && printf '%s' "$out2" | grep -q "already uses"; then
  ok "the swap: the module runs the Vu version, an int over 64 bits runs the original, a second run adds nothing"
else bad "the swap" "$out
$use
$out2"; fi

# tests/speedup: a package, refusals, exceptions, edge values, threads
t="$work/edge"; rm -rf "$t"; mkdir -p "$t/pkg"; cp "$d"/speedup/*.vu "$t/"; cp "$d/speedup/text.py" "$t/pkg/"; touch "$t/pkg/__init__.py"; cp "$d/speedup/edge.py" "$t/"
out=$(cd "$t" && PYTHON=$PY "$VU" speedup pkg/text.py:word_counts --port word_counts.vu --inputs 1500 2>&1)
if printf '%s' "$out" | grep -q "^same answers" && printf '%s' "$out" | grep -q "isn't faster here" && ! grep -q "vu speedup:" "$t/pkg/text.py"; then
  ok "a function the Vu version isn't faster at (dict through JSON): checked, and left alone"
else bad "not faster: left alone" "$out"; fi
out=$(cd "$t" && PYTHON=$PY "$VU" speedup pkg/text.py:checksum --port checksum.vu --inputs 1500 2>&1)
use=$(cd "$t" && $PY -c "import pkg.text as m; print(hasattr(m.checksum, '__vu_original__'), m.checksum(b'hello', odd=True), m.checksum(data=b'hello'))" 2>&1)
if printf '%s' "$out" | grep -q "now runs the Vu version" && grep -q "from ._vu_text import" "$t/pkg/text.py" && [ "$use" = "True 3239 99162322" ]; then
  ok "in a package (a relative import), bytes and a bool, called with keywords"
else bad "in a package" "$out
$use"; fi
out=$(cd "$t" && PYTHON=$PY "$VU" speedup edge.py:sort_in_place --port sort_in_place.vu 2>&1); rc=$?
if [ $rc -ne 0 ] && printf '%s' "$out" | grep -q "changes its arguments"; then ok "a function that changes its arguments: refused"; else bad "changes its arguments" "$out"; fi
out=$(cd "$t" && PYTHON=$PY "$VU" speedup edge.py:wrong_hint --port wrong_hint.vu 2>&1); rc=$?
if [ $rc -ne 0 ] && printf '%s' "$out" | grep -q "fix its hint"; then ok "a result that isn't its hint's type: refused"; else bad "wrong hint" "$out"; fi
out=$(cd "$t" && PYTHON=$PY "$VU" speedup edge.py:strict_word --port strict_word.vu --no-apply --inputs 1500 2>&1)
if printf '%s' "$out" | grep -q "^same answers"; then ok "an exception of the module's own class (BadWord), as the original raises it"; else bad "the module's exception" "$out"; fi
(cd "$t" && PYTHON=$PY "$VU" speedup edge.py:count_chars --port count_chars.vu --force --inputs 500 >/dev/null 2>&1 \
 && PYTHON=$PY "$VU" speedup edge.py:total --port total.vu --force --inputs 500 >/dev/null 2>&1)
use=$(cd "$t" && $PY - <<'EOF' 2>&1
import threading, edge
assert hasattr(edge.count_chars, "__vu_original__") and hasattr(edge.total, "__vu_original__")
r = [edge.count_chars("a\ud800b"), edge.count_chars("a\x00b"), edge.count_chars(type("S", (str,), {})("héllo")),
     edge.total([2**40, 2**40]) == 2 * 4**40, edge.total([2**62]) == 2**124, edge.total([True, 2]), edge.total([2**31] * 3) == 3 * 4**31]
errs = []
def work(k):
    for i in range(1500):
        xs = list(range(k, k + 40))
        if edge.total(xs) != sum(x * x for x in xs): errs.append(k)
        if i % 50 == 0 and edge.total([2**62, 1]) != 2**124 + 1: errs.append(-k)
ts = [threading.Thread(target=work, args=(k,)) for k in range(8)]
[t.start() for t in ts]; [t.join() for t in ts]
print(*r, len(errs))
EOF
)
if [ "$use" = "3 3 5 True True 5 True 0" ]; then ok "a surrogate, NUL, a str subclass, ints over 64 bits, bools; 8 threads with overflow panics in between"
else bad "edge values and threads" "$use"; fi

# Float methods and the library's pow: the same bits as Python's math module (a few hundred values)
cat > "$work/fm.vu" <<'EOF'
fn main():
  var x = 0.000123
  var out: [Str] = []
  while x < 300.0:
    out.push("{x.sin()} {x.cos()} {x.tan()} {x.atan()} {x.exp()} {x.log()} {x.log2()} {x.log10()} {x.sinh()} {x.tanh()} {x.pow(2.0)} {x.pow(0.37)} {x.atan2(1.5)}")
    x = x * 1.37 + 0.011
  print("\n".join(out))
EOF
"$VU" build "$work/fm.vu" -o "$work/fm" >/dev/null 2>&1
vu_out=$("$work/fm" 2>&1)
py_out=$($PY -c "
import math
x = 0.000123; out = []
def f(v): return repr(v) if v != int(v) or abs(v) >= 1e16 else repr(v).replace('.0', '') if repr(v).endswith('.0') else repr(v)
while x < 300.0:
    vals = [math.sin(x), math.cos(x), math.tan(x), math.atan(x), math.exp(x), math.log(x), math.log2(x), math.log10(x), math.sinh(x), math.tanh(x), x ** 2.0, math.pow(x, 0.37), math.atan2(x, 1.5)]
    out.append(' '.join(f(v) for v in vals))
    x = x * 1.37 + 0.011
print('\n'.join(out))")
if [ "$vu_out" = "$py_out" ]; then ok "Float methods (optimized build): the same bits as Python's math module and ** on $(printf '%s\n' "$vu_out" | wc -l | tr -d ' ') values each"
else printf '%s\n' "$vu_out" > "$work/fm_vu"; printf '%s\n' "$py_out" > "$work/fm_py"
  bad "Float methods against Python" "$(diff "$work/fm_vu" "$work/fm_py" | head -10)"; fi

echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
