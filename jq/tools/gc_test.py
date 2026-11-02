# Compaction inside a run (-n with inputs): programs that keep, drop and rebuild what they read,
# run by jq and by vjq compacting very often (VJQ_GC_UNITS); outputs must match.
#   python3 gc_test.py JQ VJQ INPUT.ndjson
import os, subprocess, sys
J, V, F = sys.argv[1], sys.argv[2], sys.argv[3]
progs = [
  'reduce inputs as $x (0; . + 1)',
  'reduce inputs as $x ({}; .[$x.address.city] += 1) | to_entries | sort_by(.key) | .[:5]',
  '[inputs | .id] | length, add',
  '[inputs] | length, .[0].name, .[-1].tags',
  'foreach inputs as $x (0; . + 1; select(. % 700 == 0)) ',
  'inputs | select(.id % 400 == 1) | {id, name, n: (.tags | length)}',
  'first(inputs | select(.id > 2500)) | .name',
  '[limit(5; inputs)] | map(.id)',
  'label $out | inputs | if .id > 1234 then (.id, break $out) else empty end',
  'def f: inputs; [f | .name[0:1]] | unique',
  '[inputs] as $all | $all | map(.balance) | add',
  '{x: [inputs | .id]} | .x | length',
  '[inputs | tostring] | join(",") | length',
  'reduce (inputs | .name) as $n (""; if length < 100 then . + $n else . end)',
  'reduce inputs as $x ([]; . + [$x.id]) | length',
  'reduce inputs as $x (null; if . == null or $x.balance > .balance then $x else . end) | .id',
  '[inputs | .tags[]] | group_by(.) | map([.[0], length]) | .[:3]',
  'input as $a | reduce inputs as $x ($a; .id += $x.id) | .id',
  '[inputs | select(.active)] | length',
  'reduce inputs as $x ({}; . + {($x.id | tostring): $x.name}) | length',
  'inputs | .address | keys_unsorted | join(",")',
  '[inputs | input_line_number] | .[-3:]',
  'reduce inputs as $x ([]; . + [$x] | .[-3:]) | map(.id)',
  'reduce inputs as $x (0; . + ($x | tojson | length))',
  '[inputs | .name | ascii_downcase | test("an")] | map(select(.)) | length',
  '[inputs] | sort_by(.balance) | .[0].id',
  'reduce inputs as $x ({}; .[$x.name[0:1]] |= (. // []) + [$x.id]) | map_values(length) | to_entries | .[:4]',
  '[foreach inputs as $x ({}; .[$x.address.city] = $x.id; length)] | .[-1]',
  'try (inputs | if .id == 2000 then error("stop") else empty end) catch .',
  '[inputs | .score? // 0] | add',
  'reduce inputs as $x ({a: [], b: {}}; .a += [$x.id] | .b[$x.name] = $x.balance) | (.a | length), (.b | length)',
  '[inputs | to_entries[] | .key] | unique',
  'reduce inputs as $x (""; $x.name) ',
  '[inputs|.id] | .[1000:1003]',
  '-R:reduce inputs as $l (0; . + ($l | length))',
  '-R:[inputs | fromjson | .id] | add',
  '-R:[inputs] | .[-1][0:40]',
  '-R:inputs | select(test("Berlin")) | .[0:20]',
  '-R:reduce inputs as $l ({}; .[$l[2:4]] += 1)',
]
envv = dict(os.environ)
same = 0
for p in progs:
    fl = "-nc"
    if p.startswith("-R:"): fl, p = "-nRc", p[3:]
    a = subprocess.run([J, fl, p, F], capture_output=True)
    rows = [a]
    for u in ("3000", "50000", "1000000"):
        b = subprocess.run([V, fl, p], stdin=open(F, "rb"), capture_output=True, env=dict(envv, VJQ_GC_UNITS=u)) if u == "50000" else subprocess.run([V, fl, p, F], capture_output=True, env=dict(envv, VJQ_GC_UNITS=u))
        rows.append(b)
    ok = all((r.returncode, r.stdout, r.stderr) == (a.returncode, a.stdout, a.stderr) for r in rows[1:])
    if ok: same += 1
    else:
        print("===", p); print(" jq: ", a.returncode, a.stdout[:300], a.stderr[:300])
        for r in rows[1:]: print(" vjq:", r.returncode, r.stdout[:300], r.stderr[:300])
print(f"{same}/{len(progs)} same")
