# attack.py DIR MODE N SEED [--fmt] [ARGS...]: writes N generated scripts into DIR, runs shellcheck
# and vsc on them with -f json1 (and ARGS, e.g. -o all), and prints every comment that differs in
# any field, the fix included. With --fmt: runs both in every format (tty, gcc, checkstyle, diff,
# json, json1, quiet) on chunks of 50 files and compares stdout, stderr and exit status, then
# narrows a chunk that differs down to its files.
# MODE: gen (snippets from a grammar of shell features), mut (mutated corpus files), splice
# (pieces of corpus files), tok (tokens inserted), bytes (random bytes: invalid UTF-8, NUL, CR,
# control characters), deep (deep nesting, unbalanced quotes, here-documents) or uni (generated
# scripts with characters of every Unicode category in names, operators and words)
import sys, os, random, subprocess, re, collections
# SCW: the work directory (shellcheck, vsc, corpus/, corpus2/, files.txt, ...)
W = os.environ['SCW']
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d, mode, n, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
extra_args = sys.argv[5:]
fmt_mode = '--fmt' in extra_args
extra_args = [a for a in extra_args if a != '--fmt']
import json
rnd = random.Random(seed)
src = open(HERE + '/check.vu').read() + open(HERE + '/parse.vu').read()
codes = set(re.findall(r'\b([123]\d{3}), "', src)) | set('2034 2154 2031 2120 3014 3015 3018 3028 3045 1072 1137 2144 2245'.split())

shebangs = ['#!/bin/sh', '#!/bin/bash', '#!/bin/dash', '#!/bin/busybox sh', '#!/bin/ksh', '#!/usr/bin/env bash', '']
vars_ = ['a', 'b', 'foo', 'PATH', 'RANDOM', 'UID', 'BASH_SOURCE', '_', 'HOSTNAME', 'arr', 'x1', '1', '@', '*', '#', '?']
def var(): return rnd.choice(vars_)
def expansion():
    v = var()
    return rnd.choice(['$' + v, '${' + v + '}', '${' + v + ':-x}', '${#' + v + '}', '${!' + v + '}', '${' + v + '[@]}',
        '${' + v + '[0]}', '${' + v + ':1:2}', '${' + v + '/x/y}', '${' + v + '^^}', '${' + v + ',}', '${!' + v + '*}',
        '${!' + v + '[@]}', '${' + v + '%%.*}', '${' + v + '#*/}', '$(echo ' + v + ')', '`echo $' + v + '`', '$((' + v + '+1))',
        '$(<file)', '$[1+2]', "$'\\n'", '$"msg"', '~/x', '"~/x"', "'~/x'"])
def word():
    r = rnd.random()
    if r < 0.3: return expansion()
    if r < 0.45: return '"' + rnd.choice(['', 'x ', 'a b']) + expansion() + '"'
    if r < 0.55: return rnd.choice(['*.txt', '[abc]', '[a-z]', '[^x]', '[[:digit:]]', '[:alpha:]', '{a,b}', '{1..3}', '"$d"/*', '@(a|b)', '[aa]'])
    if r < 0.65: return rnd.choice(['-n', '-e', '-x', '-o', '-r', '-p', '--', '-E', '-ne', '-s', '-v', '-a', '-L', '-f'])
    if r < 0.75: return "'" + rnd.choice(['$x', 'a b', "it's", '`x`', '\\n', '~/f']) + "'"
    return rnd.choice(['foo', 'bar', 'x', '1', '0', '42', 'file', 'ls', '=', 'a"b"c', '"a""b"', '"a"b"c"', "'a'b", 'z=1'])
cmds = ['expr', 'mv', 'cp', 'ln', 'chmod', 'rm -rf', 'su', 'mkdir -pm 700', 'time', 'egrep', 'which', 'tempfile', 'echo', 'printf', 'read', 'cd', 'local', 'declare', 'export', 'readonly', 'trap', 'set', 'test', 'let', 'source', '.',
        'exec', 'unset', 'eval', 'grep', 'ls', 'find', 'xargs', 'tr', 'sed', 'cat', 'rm', 'wait', 'type', 'hash', 'ulimit', 'umask',
        'jobs', 'mapfile', 'shopt', 'typeset', 'pushd', 'kill', 'command', 'builtin', 'exit', 'return', 'sudo', 'ssh', 'alias', 'getopts']
def simple():
    c = rnd.choice(cmds)
    args = [word() for _ in range(rnd.randint(0, 3))]
    if c == 'trap': args = [rnd.choice(["'echo hi'", '"rm $f"', '-', "''"])] + [rnd.choice(['ERR', 'int', 'SIGINT', 'EXIT', 'debug', 'RETURN', 'TERM'])]
    if c == 'set': args = [rnd.choice(['-e', '-o', '+o', '-eo', '-x', '--', '-E', '-u', '--foo', '-ao', '-k', '+x'])] + [rnd.choice(['pipefail', 'errexit', 'nounset', 'x', '-u', 'vi'])]
    if c == 'printf' and rnd.random() < 0.5: args = [rnd.choice(['"%s\\n"', "'%q'", '"$fmt"', '"%d %s"', '"x"', "'%s %s'"])] + args
    s = ' '.join([c] + args)
    if rnd.random() < 0.2: s = rnd.choice(['a=1 ', 'a+=1 ', 'arr=(1 2) ', 'x=$y ']) + s
    if rnd.random() < 0.25: s += ' ' + rnd.choice(['> out', '>> log', '2>&1', '&> f', '>& f', '>&2', '2>&1 > f', '> f 2>&1', '< <(ls)', '<<< "$x"', '9> f', '10> f', '{fd}> f', '> /dev/tcp/h/1', '> *.log', '> ls', '| grep x', '|& cat', '| wc -l'])
    return s
def test():
    op = rnd.choice(['==', '=', '!=', '<', '>', '\\<', '-eq', '-lt', '=~', '-nt', '-gt'])
    uop = rnd.choice(['-n', '-z', '-v', '-a', '-o', '-R', '-N', '-k', '-G', '-O', '-e', '-f', '-d'])
    e = rnd.choice([word() + ' ' + op + ' ' + word(), uop + ' ' + word(), word(), word() + ' -a ' + word(), word() + ' -o ' + word(),
                    '"$(grep x f)"', '-n "$(ls | grep y)"', '-z "$(grep -c z)"', word() + ' && ' + word(), word() + ' || ' + word(), '$x == $y', 'x$a = xfoo'])
    return rnd.choice(['[ ' + e + ' ]', '[[ ' + e + ' ]]', 'test ' + e])
def stmt(depth=0):
    r = rnd.random()
    if depth < 2 and r < 0.08: return 'if ' + test() + '; then\n  ' + stmt(depth + 1) + '\nfi'
    if depth < 2 and r < 0.13: return 'for f in ' + ' '.join(word() for _ in range(rnd.randint(1, 3))) + '; do\n  ' + stmt(depth + 1) + '\ndone'
    if depth < 2 and r < 0.16: return 'f' + str(rnd.randint(0, 2)) + '() {\n  ' + stmt(depth + 1) + '\n  ' + stmt(depth + 1) + '\n}'
    if depth < 2 and r < 0.18: return 'while read -r line; do\n  ' + stmt(depth + 1) + '\ndone < file'
    if depth < 2 and r < 0.20: return 'case ' + word() + ' in\n  ' + word() + ') ' + stmt(depth + 1) + ' ;;\n  *) ' + stmt(depth + 1) + ' ;;\nesac'
    if r < 0.30: return test() + ' && ' + simple() + rnd.choice(['', ' || ' + simple()])
    if r < 0.36: return rnd.choice(['((i++))', 'echo $((i**2))', 'echo $((2#101))', 'for ((i=0;i<3;i++)); do :; done', 'select x in a b; do :; done', 'coproc cat', 'my-fn() { :; }', 'arr=(a b c)', 'x=$((++i))', 'echo $((x--))'])
    if r < 0.42: return var().strip('@*#?1') + '=' + word() if var().strip('@*#?1') else 'z=' + word()
    if r < 0.46: return 'echo "$(echo ' + word() + ')"'
    if r < 0.50: return 'cmd >> f\ncmd2 >> f\ncmd3 >> f'
    if r < 0.56: return rnd.choice(['ls | grep x', 'ls -l | wc -l', 'ls -N | head', 'find . | xargs rm', 'find . -print0 | xargs -0 rm',
        'ps aux | grep foo', 'ps -p 1 | grep x', 'grep x f | wc -l', 'grep -c x f | wc', 'ls | xargs echo', 'a=ls -l', 'a=*.txt cmd', 'x=pwd',
        'x=$x', 'x="${x}"', 'x=$x cmd', 'v=1 echo $v', 'v=$v cmd', '( [ -f x ] )', '( [ a ] && [ b ] )', 'if ( test -f x ); then :; fi',
        'f() ( [ x ] )', '( [[ ${v:=1} ]] )', 'echo $(foo > bar)', 'v=$(foo 2>&1 > /dev/null)', 'v=`foo >> log`', 'v=$(cat <&3)',
        '$(true)', '`true`', '$((i++))', 'echo ${foo$n}', 'echo ${$x}', 'echo ${${x}}', 'echo ${"x"}', "echo ${'x'}", 'echo ${$(x)}',
        'echo ${var${n}_x}', 'echo ${-x}', 'find . -name *.sh', 'find . -iname "*.sh"', '. ./lib.sh arg', 'for f in "$@"; do :; done',
        'for f in "*.txt"; do :; done', 'for f in "$x"; do :; done', "for f in 'a b'; do :; done", 'for f in a,b; do :; done',
        'for f in a, b; do :; done', 'for f in $(cat f); do :; done', 'for f in $(ls); do :; done', 'for f in $(find .); do :; done',
        'case $x in $y) :;; "$z") :;; *$w*) :;; esac', '[ -e *.txt ]', '[[ -e *.txt ]]', '[ -v x* ]', '[ $a -eq 2*3 ]', '[ "${a[@]}" = x ]',
        '[[ $@ == x ]]', '[ {a,b} = a ]', '[[ x == {a,b} ]]', '[ *.c ]', '[[ *.c ]]', '[[ $x = $y ]]'])
    return simple()

extras = [
    'expr 1 + 2', 'expr $a \\* 2', 'expr "$x" : *.c', 'expr length "$s"', 'expr match $a b', 'expr 1', 'x=$(expr $a + 1)',
    'while getopts "ab:c" opt; do\n  case $opt in\n    a) :;;\n    d) :;;\n  esac\ndone',
    'while getopts ":ab" o; do case "$o" in a) :;; b) :;; \\?) :;; esac; done',
    'rm -rf "$dir/"', 'rm -rf /usr/local', 'rm -r "$x"/*', 'rm -rf ${a:?}/', 'mv "$f"', 'cp -t dir f', 'ln -s x',
    'sudo echo x > /etc/f', 'sudo cd /', 'chmod -r 644 f', 'xargs -i echo {}', 'eval "${arr[@]}"', 'eval "${arr[@]@Q}"',
    'time -p ls', 'time ls | grep x', 'local x=1', 'function f { :; }', 'function g() { :; }', 'PATH=/my/bin', 'PATH="~/bin:$PATH"',
    "IFS='\\n'", 'IFS="\\t"', 'for i in a; do for i in b; do :; done; done', 'for ((i=0;i<2;i++)); do for i in x; do :; done; done',
    'echo x ]', 'echo [ x ]]', 'cd foo\nls\ncd ..', 'break', 'f() { continue; }', 'echo $[1+2]', 'ssh host <<EOF\necho $x\nEOF',
    "alias ll='ls -l'; ll", 'alias a=b\na', '[ -f x ]; echo $?', 'test -d y\nexit $?', 'echo hi; echo $?', 'printf x; r=$?',
    'later\nlater() { :; }', 'n=1; n+=1', 'n=1; m+=$n', 'declare -i k; k+=1', 'arr=(a=1 2=b)', 'declare -A m; m=(x y)', 'a=([1]= x)',
    'a[$((i+1))]=1', 'echo $(( (x) ))', 'echo $(( ((x)) ))', 'for (((i)=0;;)); do :; done', '[ -a file ]', '[ ! -a file ]', '[ ! -o x ]',
    '! ! true', 'true | ! false', 'f() { f; }', 'f() { f x & }', '[ x ] | [ y ]', '[ x ] &', '[[ $x != a ]] || [[ $x != b ]]',
    '[ "$x" = a ] && [ "$x" = b ]', '(( x == 1 && x == 2 ))', '(( x != 1 || x != 2 ))', '[ $x != a -o $x != b ]', '[ $x = a -a $x = b ]',
    '[ x -foo y ]', '[ -Q x ]', 'test 1 > 2', 'PS1="\\e[31m$ "', 'echo {1..$n}', 'eval echo {$a..3}', 'a[1][2]=x', 'echo ${a[1][2]}',
    '[ "$(ls)" ]', '[ "$var" ]', '[ ! -n "$x" ]', '! [ -z "$x" ]', '[[ ! $a -eq 1 ]]', '! [ "$a" = b ]', 'case $x in a) :;; esac',
    'cat file | grep x', 'cat "$f" | wc', 'set -e\nf() { :; }\nf && echo\nx=$(f)\nif f; then :; fi', 'set -e\n! true\ntrue',
    'v=$(false) ; local y=$(false)', 'echo "$(false)" "$(true)"', 'x=$(a) y=$(b)', 'echo $(a | b)', 'set -o pipefail; a | b | c',
    '$x=1', '${y}=2', '$0=x', '0=x', '2=x', '9foo=1', 'a${b}c=1', 'a==b', '===', '=foo', '====', 'echo= 1', '"" x', 'foo/ x',
    'foo, x', 'foo# x', "$'a\\tb' x", 'f() { local a=1 b=$a; }', 'declare x=1 y=$x', 'export a=1 a=2', 'local declare x',
    'echo   a   b', 'echo a     b > f', 'grep -E *.c f', 'grep "a*" f', 'grep x* f', 'grep -F a* f', 'unset arr[1]', 'find -name x',
    'find . -exec sh -c "echo {}" \\;', 'find . -exec "echo {} |" \\;', 'find . -name a -o -name b -exec rm {} +', 'find . -exec echo $(x)',
    'return 300', 'exit -1', 'exit 1 2', 'return $x', 'trap "" 9', 'trap x 20', 'trap - kill', 'set x y', 'set a=b', 'export $x',
    'read $v', 'read -a arr[1]', 'alias x="echo $1"', 'echo hi | sleep 1', 'ls < f', 'echo x | cmd > f', 'cmd < a < b', 'a | b > f | c',
    'x=1 > f', 'echo ${#}', 'echo "$x"; x+=$x', 'echo $((012 + 09))', 'echo $((a/b*c))', '[ 1 -lt 2.5 ]', '[[ $x < 3 ]]', '[ $a \\> 1 ]',
    '[ x -lt y ]', '[[ x -gt y ]]', 'q=1; [[ q -gt 2 ]]', '[ "$x" -eq "1" ]', '[ 0 ]', '[ true ]', '[ "x" ]', '[ x = y ]', '[ a = b* ]',
    '[[ x=y ]]', '[ -n "a$x" ]', '[ -z "foo" ]', '[ -n $x ]', '[ $a = $b ]', '[ 1 -eq "$x" ]', '([ -f x ])', '(-f x)', '(x = y)',
    'case $x in a|b) ;; a) ;; esac', 'case x in a) ;; esac', 'case $x in *) ;; a) ;; esac', 'case "$x" in "$y") ;; esac',
    'for f in "${arr[@]}"; do echo ${arr[$f]}; done', 'for k in "${a[@]}"; do (( b[k]++ )); done', '((a = 1))', 'echo ${x:?} > f',
    'f() { :; }; sudo f', 'g() { :; }; xargs g', 'while read l; do ssh h; done < f', 'while read l; do ffmpeg -i x; done',
    'while read l; do HandBrakeCLI; done < f', 'exec foo\necho bar', 'exec 3>f\necho x', 'if x; then exec a; fi\necho', 'cmd |& cat',
    'echo "${x}" >&2 2>&1', 'ls 2>&1 >f', 'echo $"x"', 'echo $"$v"', 'x=1\necho $"x"', 'echo $"(ls)"',
]
def gen():
    lines = [rnd.choice(shebangs)]
    if rnd.random() < 0.1: lines.append('# shellcheck disable=SC' + rnd.choice(sorted(codes)))
    if rnd.random() < 0.1: lines.append('# shellcheck shell=' + rnd.choice(['sh', 'bash', 'dash', 'ksh']))
    for _ in range(rnd.randint(1, 8)): lines.append(stmt() if rnd.random() < 0.6 else rnd.choice(extras))
    return '\n'.join(lines) + '\n'
corpus = [('corpus', l.strip()) for l in open(W + '/files.txt')] + [('corpus2', l.strip()) for l in open(W + '/files2.txt')]
if os.path.exists(W + '/files3.txt'): corpus += [('corpus3', l.strip()) for l in open(W + '/files3.txt')]
def pick():
    d, f = rnd.choice(corpus)
    return W + '/' + d + '/' + f
def mut():
    while True:
        base = pick()
        try: b = open(base, 'rb').read()
        except OSError: continue
        if 0 < len(b) < 20000: break
    b = bytearray(b)
    for _ in range(rnd.randint(1, 4)):
        if not b: break
        i = rnd.randrange(len(b))
        op = rnd.random()
        if op < 0.4: del b[i:i + rnd.randint(1, 5)]
        elif op < 0.7: b[i:i] = rnd.choice([b'"', b"'", b'`', b'(', b')', b'{', b'}', b'[', b']', b'$', b'\\', b'\n', b';', b'&', b'|', b'<<EOF', b'fi', b'done', b'#', b'\t', b' ', b'$(', b'${'])
        else:
            j = rnd.randrange(len(b)); k = rnd.randint(1, 30)
            b[i:i] = b[j:j + k]
    return bytes(b)
def readc():
    while True:
        base = pick()
        try: b = open(base, 'rb').read()
        except OSError: continue
        if 0 < len(b) < 60000: return b
def splice():
    out = [rnd.choice(shebangs).encode()]
    for _ in range(rnd.randint(2, 4)):
        ls = readc().split(b'\n')
        i = rnd.randrange(len(ls)); k = rnd.randint(1, 40)
        out += ls[i:i + k]
    return b'\n'.join(out) + b'\n'
toks = [b'if', b'then', b'fi', b'do', b'done', b'case', b'esac', b'in', b'{', b'}', b'(', b')', b'((', b'))', b'[[', b']]', b'[', b']',
        b';;', b'&&', b'||', b'|', b'&', b';', b'<<', b'<<-', b'>', b'>>', b'<(', b'$(', b'`', b'"', b"'", b'${', b'$((', b'function',
        b'!', b'=', b'+=', b'=~', b'-eq', b'\\', b'\n', b'# shellcheck disable=SC2086', b'local', b'export x', b'elif', b'else', b'select', b'coproc']
def tok():
    b = bytearray(readc())
    for _ in range(rnd.randint(1, 3)):
        sp = [m.start() for m in re.finditer(rb'[ \n]', bytes(b))]
        if not sp: break
        i = rnd.choice(sp)
        t = rnd.choice(toks)
        if rnd.random() < 0.5:
            j = bytes(b).find(b' ', i + 1)
            if 0 < j - i < 20: del b[i + 1:j]
        b[i + 1:i + 1] = t + b' '
    return bytes(b)
def rbytes():
    b = bytearray(readc())
    for _ in range(rnd.randint(1, 6)):
        i = rnd.randrange(len(b) + 1)
        b[i:i] = rnd.choice([bytes([rnd.randrange(256)]), b'\xff', b'\xc3', b'\xc3\xa9', b'\xe2\x80\x99', b'\xed\xa0\x80',
            b'\xc0\x80', b'\xf4\x90\x80\x80', b'\x00', b'\r', b'\r\n', b'\x1b[1m', b'\t', b'\xef\xbb\xbf', b'\x0c', b'\xa0',
            b'\xe2\x80\x9c', b'\xc2\xa0', b'\x7f'])
    return bytes(b)
# characters of every category GHC's Data.Char tells apart: letters (Lu Ll Lt Lm Lo), digits and
# other numbers, marks, spaces (Zs, Zl, Zp), format and private-use characters, case pairs whose
# simple mappings differ from the full ones, surrogates and characters past the BMP
UNI = ['\u00e9', '\u00c9', '\u01c5', '\u01c6', '\u02b0', '\u05d0', '\u4e2d', '\u0661', '\u2163', '\u00b2', '\u0301', '\u00a0',
       '\u2003', '\u3000', '\u2028', '\u2029', '\u200b', '\ue000', '\u0130', '\u00df', '\u1e9e', '\u03a3', '\u03c2', '\u212a',
       '\U0001d400', '\U0001f600', '\U0002ebf0', '\u24b6', '\u2019', '\u201c', '\u2013', '\u00ad', '\u0149', '\u1f80', '\u1680']
def uni():
    t = gen()
    out = []
    for ch in t:
        if ch.isalpha() and rnd.random() < 0.08: out.append(rnd.choice(UNI))
        elif ch == ' ' and rnd.random() < 0.03: out.append(rnd.choice(UNI))
        else: out.append(ch)
    if rnd.random() < 0.3:
        out.append(rnd.choice(['$' + rnd.choice(UNI) + 'x\n', 'echo "${' + rnd.choice(UNI) + 'a}"\n', 'set -' + rnd.choice(UNI) + 'e\n',
            'trap x ' + rnd.choice(UNI) + 'int\n', 'tr ' + rnd.choice(UNI) * 2 + ' x\n', 'f' + rnd.choice(UNI) + '() { :; }\n',
            '[ -' + rnd.choice(UNI) + ' x ]\n', 'cat <<E' + rnd.choice(UNI) + '\nx\ne' + rnd.choice(UNI) + '\n',
            'kill -' + rnd.choice(UNI) + ' 1\n', 'X' + rnd.choice(UNI) + '=1; echo "$x' + rnd.choice(UNI) + '"\n']))
    return ''.join(out)
def deep():
    k = rnd.randint(1, 60)
    kind = rnd.randrange(8)
    lines = [rnd.choice(shebangs)]
    if kind == 0: lines.append('if true; then ' * k + 'echo $x' + '; fi' * rnd.choice([k, k - 1, k + 1]))
    elif kind == 1: lines.append('$(' * k + 'echo $y' + ')' * rnd.choice([k, k - 1]))
    elif kind == 2: lines.append('echo ' + '"$(' * k + 'ls' + ')"' * rnd.choice([k, k - 1]))
    elif kind == 3: lines.append('{ ' * k + 'a=1; ' + '} ' * rnd.choice([k, k - 1, k + 1]))
    elif kind == 4:
        for i in range(k): lines.append(f'cat <<{"-" if i % 2 else ""}E{i}\n$x{i} `y`\n' + ('\t' if i % 2 else '') + f'E{i}' * rnd.choice([1, 1, 0]))
    elif kind == 5: lines.append('echo ' + rnd.choice(['"', "'", '`', '$(', '${', '((']) * rnd.randint(1, 5) + ' x ' + rnd.choice(['', '"', "'"]))
    elif kind == 6: lines.append('f() { ' * k + 'g; ' + '}; ' * k + 'f')
    else: lines.append('(' * k + 'echo' + ')' * rnd.choice([k, k - 1, k + 1]))
    if rnd.random() < 0.5: lines.append(gen())
    return '\n'.join(lines) + '\n'
os.makedirs(d, exist_ok=True)
names = []
for k in range(n):
    p = f'{d}/t{k}.sh'
    data = gen().encode() if mode == 'gen' else mut() if mode == 'mut' else splice() if mode == 'splice' else rbytes() if mode == 'bytes' else deep().encode() if mode == 'deep' else uni().encode('utf-8', 'surrogatepass') if mode == 'uni' else tok()
    open(p, 'wb').write(data)
    names.append(p)
def run(cmd, chunk):
    out = collections.defaultdict(list)
    for i in range(0, len(names), chunk):
        r = subprocess.run(cmd + names[i:i + chunk], capture_output=True, timeout=3000)
        try: cs = json.loads(r.stdout.decode('utf-8', 'surrogateescape'))['comments']
        except Exception: cs = []
        for c in cs: out[c['file']].append(json.dumps(c, ensure_ascii=False))
    return out
def run_all(tool, fmt, files):
    r = subprocess.run([tool, '-f', fmt] + extra_args + files, capture_output=True, timeout=3000)
    return r.stdout, r.stderr, r.returncode
if fmt_mode:
    bad = 0
    for fmt in ['tty', 'gcc', 'checkstyle', 'diff', 'json', 'json1', 'quiet']:
        for i in range(0, len(names), 50):
            chunk = names[i:i + 50]
            if run_all(W + '/shellcheck', fmt, chunk) == run_all(W + '/vsc', fmt, chunk): continue
            single = 0
            for p in chunk:
                a, b = run_all(W + '/shellcheck', fmt, [p]), run_all(W + '/vsc', fmt, [p])
                if a != b:
                    bad += 1
                    single += 1
                    print('==', fmt, p, 'exit', a[2], b[2], 'stdout same' if a[0] == b[0] else 'stdout differs', 'stderr same' if a[1] == b[1] else 'stderr differs')
            if single == 0:
                bad += 1
                print('==', fmt, 'chunk', i, 'differs only as a whole')
    print(f'{bad} (format, file) pairs differ of {n} files x 7 formats', file=sys.stderr)
    sys.exit(0)
ref = run([W + '/shellcheck', '-f', 'json1'] + extra_args, 200)
vsc = run([W + '/vsc', '-f', 'json1'] + extra_args, 2000)
bad = 0
for p in names:
    a, b = sorted(ref.get(p, [])), sorted(vsc.get(p, []))
    if a != b:
        bad += 1
        print('==', p)
        sa, sb = set(a), set(b)
        for l in a:
            if l not in sb: print('  miss', l)
        for l in b:
            if l not in sa: print('  extra', l)
        if sa == sb: print('  (dup differs)')
print(f'{bad} of {n} files differ', file=sys.stderr)
