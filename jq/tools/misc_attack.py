# Attack round: formats, dates (with TZ), output and input options, arguments, exit codes, odd
# JSON (deep, big numbers, bad UTF-8, escapes). Each case runs in jq 1.7.1 and vjq (as "jq");
# stdout, stderr and exit status must match.   python3 misc_attack.py JQ VJQ [FILTER]
import itertools, json, os, subprocess, sys, tempfile
J, V = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
flt = sys.argv[3] if len(sys.argv) > 3 else ""
work = tempfile.mkdtemp()
def wfile(name, data):
    p = os.path.join(work, name)
    with open(p, "wb") as f: f.write(data if isinstance(data, bytes) else data.encode())
    return p
cases = []   # (args, stdin bytes, env)
def add(args, inp=b"", env=None): cases.append((args, inp if isinstance(inp, bytes) else inp.encode(), env or {}))
vals = ['null', 'true', 'false', '0', '-0', '1.5', '-1e-7', '1e1000', '100000000000000000001', '"plain"',
        '"a,b\\"c\\td\\ne"', '"<&\'\\">"', '"ü日🎉"', '"\\u0000x"', '"é a=b&c?d/e"', '[1,"a,b",null,true,1.5]',
        '["x\\ty","a\\\\b",[1]]', '{"a":1}', '[[1,2]]', '[]', '""', '"YW55IGNhcm5hbCBwbGVhcw=="', '"YW55"', '"!!"',
        '"=="', '"\\ud83d\\ude00"', '[{"a":1}]', '"$(rm -rf /)"', '"it\'s"', '["a b", "c\'d"]']
fmts = ["@text", "@json", "@html", "@uri", "@csv", "@tsv", "@sh", "@base64", "@base64d"]
for v in vals:
    add(["-nr", f'{v} | ({fmts[0]}, {fmts[1]}, {fmts[2]}, {fmts[3]})'])
    for f in fmts[4:]:
        add(["-nr", f'{v} | try {f} catch "ERR: \\(.)"'])
    add(["-nr", f'{v} as $x | @csv "x\\($x)y", @sh "a \\($x) b", @json "j\\($x)", @base64 "b\\($x)"'])
# dates
tfmts = ["%a %A %b %B", "%c", "%C %d %D %e", "%F %g %G %h", "%H %I %j %k %l", "%m %M %n %p", "%r %R", "%s %S %t %T",
         "%u %U %V %w %W", "%x %X %y %Y", "%z %Z %%", "%Ec %EY %Od", "%+", "%Q", "", "%", "x%Yy"]
times = ['0', '1425599621', '-1', '1e10', '1425599621.123', '"2015-03-05T23:51:47Z"', '[2015,2,5,23,51,47,4,63]',
         '[2015,2,5]', '[1970,0,1,0,0,0,0,0]', '[2024,1,29,12,0,0.5,4,59]', 'null', '"x"', '[]', '[2015,"a"]', '1e300']
for tz in [None, "UTC", "America/New_York", "Asia/Kolkata", "Europe/London", "Australia/Lord_Howe"]:
    env = {"TZ": tz} if tz else {}
    for t in times:
        add(["-nc", f'{t} | [try todate catch "E:\\(.)", try gmtime catch "E:\\(.)", try (gmtime|mktime) catch "E:\\(.)", try localtime catch "E:\\(.)", try (gmtime|todate) catch "E:\\(.)"]'], env=env)
        for f in tfmts:
            add(["-nc", f'{t} | [try strftime({json.dumps(f)}) catch "E:\\(.)", try strflocaltime({json.dumps(f)}) catch "E:\\(.)"]'], env=env)
    for s, f in [("2015-03-05T23:51:47Z", "%Y-%m-%dT%H:%M:%SZ"), ("10:15", "%H:%M"), ("Thu, 05 Mar 2015 23:51:47", "%a, %d %b %Y %H:%M:%S"),
                 ("2015 64", "%Y %j"), ("1425599621", "%s"), ("x", "%Y"), ("2015-03-05 +0100", "%Y-%m-%d %z"), ("12/31/99", "%D"),
                 ("2015-03-05T23:51:47.123Z", "%Y-%m-%dT%H:%M:%S.%fZ"), ("  2015", "%Y"), ("2015-02-30", "%Y-%m-%d"), ("PM 3", "%p %I")]:
        add(["-nc", f'{json.dumps(s)} | [try strptime({json.dumps(f)}) catch "E:\\(.)", try (strptime({json.dumps(f)})|mktime) catch "E:\\(.)", try (strptime({json.dumps(f)})|todate) catch "E:\\(.)"]'], env=env)
    add(["-nc", '"2015-03-05T23:51:47Z" | [fromdate, fromdateiso8601, (fromdate|todateiso8601), dateadd("seconds"; 3)?, (try date catch .)]'], env=env)
# output options
doc = '{"b":[1,{"z":null,"a":"x\\u0001\\u001f\\u007f\\u00ff\\ud83d\\ude00"}],"a":true,"c":-0,"d":1.10,"e":[],"f":{},"g":"tab\\there"}\n"str"\n12\n[[]]\n'
opts = [[], ["-c"], ["--tab"], ["--indent", "0"], ["--indent", "1"], ["--indent", "7"], ["-S"], ["-a"], ["-j"], ["-r"],
        ["--raw-output0"], ["-C"], ["--seq"], ["-M"], ["-c", "-S", "-a"], ["-r", "-a"], ["-C", "-S", "--tab"], ["-j", "-a"],
        ["-C", "-c"], ["--seq", "-c"], ["-r", "--seq"], ["--indent", "3", "-C"], ["-e"], ["--unbuffered", "-c"]]
for o in opts:
    add(o + ["."], doc)
    add(o + [".[]?"], doc)
for colors in ["1;31", "0;31:0;32:0;33:0;34:0;35:0;36:0;37:1;37", "4;31:5", "", "garbage", "1;31:2:3:4:5:6:7:8:9", "38;5;196"]:
    add(["-C", "."], doc, {"JQ_COLORS": colors})
add(["-C", "."], doc, {"NO_COLOR": "1"})
# input options
inputs = ['1 2 3', '[1,[2,3]] {"a":{"b":null}}', '{"a":[1,', '"\\ud800"', '"\\udc00\\ud800x"', '"\xff\xfe"', '[1,2] x',
          '\x1e1\n\x1e[2]\n', '1\n\n2\r\n3', '', '   ', 'nul', 'true false null', '{"a":1,"a":2}', '[1e1000,-1e1000,1e-400]',
          '100000000000000000000000001 0.10 1.0e2 -0 -0.0 0e10', '{"\xc3\x28":1}', '"\\u00e9\\u0065\\u0301"']
for inp in inputs:
    for o in [["-c", "."], ["-c", "--stream", "."], ["-c", "--seq", "."], ["-R", "."], ["-s", "-c", "."], ["-Rs", "."],
              ["-n", "-c", "[inputs]"], ["-n", "-c", "input"], ["-c", "--stream-errors", "."], ["-c", "tojson"], ["-c", "[.[]?]"],
              ["-c", "tostream"], ["-c", ". as $x | [paths]"], ["-c", "--seq", "--stream", "."], ["-e", "."]]:
        add(o, inp.encode("latin-1") if any(ord(ch) > 127 for ch in inp) and "\\" not in inp and ord(max(inp)) < 256 else inp)
# deep and big
for d in [100, 255, 256, 257, 1000, 9999, 10000, 10001, 20000]:
    add(["-c", "."], "[" * d + "]" * d)
    add(["."], "[" * d + "]" * d)
    add(["-c", "length"], '{"a":' * d + "1" + "}" * d)
add(["-c", "[limit(3; repeat(.))] | length"], "1")
add(["-c", "reduce range(3000) as $i ([]; . + [$i]) | length"], "null")
add(["-c", "[range(300)] | reduce .[] as $x (null; [$x, .]) | tojson | length"], "null")
add(["-c", "[range(300)] | reduce .[] as $x (null; [$x, .])"], "null")
add(["-c", "tojson | fromjson"], "[" * 300 + "]" * 300)
add(["-c", "[paths] | length"], "[" * 300 + "]" * 300)
# numbers at the edges
for n in ["1e308", "1.7976931348623157e308", "1.7976931348623159e308", "5e-324", "2e-324", "9007199254740993", "-9007199254740993",
          "123456789012345678901234567890", "0.1", "1e-7", "1e17", "1.5e300", "3.0", "3.00", "-0", "1E+2", "1e+02", "0.000001", "1e-5",
          "12345678901234567", "4.94e-324", "1.0000000000000002", "18446744073709551616", "-1e-400"]:
    add(["-c", "., . + 0, -., . * 1, tostring, tojson, (. | floor), (. % 7)?, [.] , {a: .}, (. == 1e308), (. < 1)"], n)
    add(["-c", "--arg", "x", n, "$x | tonumber, (tonumber | tostring)"])
    add(["-c", "--argjson", "x", n, "$x, ($x|tojson)", "-n"])
# arguments
f1 = wfile("vals.json", '1 [2] {"a":3}\n')
f2 = wfile("raw.txt", "line1\nline2\xff\n".encode("latin-1"))
f3 = wfile("bad.json", '1 [2')
f4 = wfile("empty", "")
for a in [["--arg", "x", "v"], ["--argjson", "x", '{"a":[1]}'], ["--argjson", "x", "nan"], ["--argjson", "x", "1 2"],
          ["--slurpfile", "x", f1], ["--slurpfile", "x", f3], ["--slurpfile", "x", f4], ["--rawfile", "x", f2], ["--rawfile", "x", f4],
          ["--rawfile", "x", "/nonexistent"], ["--slurpfile", "x", "/nonexistent"], ["--args"], ["--jsonargs"]]:
    add(["-nc"] + a + ["[$__prog_args?, $ARGS, ($x? // null)]", "a", "1", "[2]"])
    add(["-nc", "$ARGS"] + a + ["p1", "{}", "null"])
add(["-nc", "$ARGS", "--args", "a", "--jsonargs", "1", "--args", "b"])
add(["-nc", "--jsonargs", "$ARGS", "1", "bad json"])
add(["-n", "--arg", "x"])
add(["-n", "--argjson", "x", "{bad"])
add(["-nc", "--arg", "x", "1", "--arg", "x", "2", "$x, $ARGS.named"])
add(["-nc", "--arg", "ENV", "1", "$ENV | type"])
add(["-nc", "--arg", "__loc__", "1", "$__loc__"])
add(["-nc", "$ENV.PATH == env.PATH, ($ENV|type), (env|type), $ENV.VJQ_TEST_X, env.VJQ_TEST_X"], env={"VJQ_TEST_X": "é=x"})
# exit codes, halt, errors
for p in ['null', 'false', 'empty', '1', 'error("x")', '1, null', 'null, 1', 'halt', '"bye\\n" | halt_error', '{"a":1} | halt_error',
          '"x" | halt_error(3)', 'null | halt_error(0)', '1 | halt_error(-1)', 'halt_error(300)', '"x" | halt_error("a")', 'error(null)',
          'error({"a":1})', 'error', '1, error("x"), 2', 'input', 'first(inputs)', '[inputs]', 'try error("x") catch halt_error(4)',
          'label $f | break $f', '"\\u0000a" | halt_error', 'error("a\\u0000b")', '[.[] | error]?', '.a.b.c = 1', '$__loc__ | halt_error']:
    for o in [[], ["-e"], ["-n"], ["-ne"], ["-c", "--seq"]]:
        add(o + [p], "1 2")
same = 0
tot = 0
for args, inp, env in cases:
    if flt and flt not in " ".join(args): continue
    tot += 1
    r = []
    for b in (J, V):
        e = dict(os.environ); e.pop("NO_COLOR", None); e.pop("JQ_COLORS", None); e.update(env)
        try:
            p = subprocess.run(["jq"] + args, executable=b, input=inp, capture_output=True, env=e, timeout=60, cwd=work)
            r.append((p.returncode, p.stdout, p.stderr))
        except subprocess.TimeoutExpired:
            r.append(("timeout", b"", b""))
    if r[0] == r[1]: same += 1
    else:
        print("=== ", json.dumps(args)[:300], repr(inp[:80]), env)
        print(" jq: ", r[0][0], r[0][1][:400], r[0][2][:300]); print(" vjq:", r[1][0], r[1][1][:400], r[1][2][:300])
print(f"{same}/{tot} same")
