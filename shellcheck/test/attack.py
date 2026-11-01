# attack.py DIR MODE N SEED: writes N generated scripts into DIR, runs shellcheck and vsc on them,
# and prints every difference in the codes vsc implements.
# MODE: gen (snippets from a grammar of shell features) or mut (mutated corpus files)
import sys, os, random, subprocess, re, collections
# SCW: the work directory (shellcheck, vsc, corpus/, corpus2/, files.txt, ...)
W = os.environ['SCW']
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d, mode, n, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
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
cmds = ['echo', 'printf', 'read', 'cd', 'local', 'declare', 'export', 'readonly', 'trap', 'set', 'test', 'let', 'source', '.',
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
def gen():
    lines = [rnd.choice(shebangs)]
    if rnd.random() < 0.1: lines.append('# shellcheck disable=SC' + rnd.choice(sorted(codes)))
    if rnd.random() < 0.1: lines.append('# shellcheck shell=' + rnd.choice(['sh', 'bash', 'dash', 'ksh']))
    for _ in range(rnd.randint(1, 8)): lines.append(stmt())
    return '\n'.join(lines) + '\n'
corpus = [l.strip() for l in open(W + '/files.txt')] + [l.strip() for l in open(W + '/files2.txt')]
def mut():
    while True:
        f = rnd.choice(corpus)
        base = W + ('/corpus/' if os.path.exists(W + '/corpus/' + f) else '/corpus2/') + f
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
        f = rnd.choice(corpus)
        base = W + ('/corpus/' if os.path.exists(W + '/corpus/' + f) else '/corpus2/') + f
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
os.makedirs(d, exist_ok=True)
names = []
for k in range(n):
    p = f'{d}/t{k}.sh'
    data = gen().encode() if mode == 'gen' else mut() if mode == 'mut' else splice() if mode == 'splice' else tok()
    open(p, 'wb').write(data)
    names.append(p)
pat = re.compile(r'^(.*?):(\d+):(\d+): (\w+): (.*) \[SC(\d+)\]$')
def run(cmd, chunk):
    out = collections.defaultdict(list)
    for i in range(0, len(names), chunk):
        r = subprocess.run(cmd + names[i:i + chunk], capture_output=True, timeout=3000)
        for l in r.stdout.decode('utf-8', 'surrogateescape').split('\n'):
            m = pat.match(l)
            if m and m.group(6) in codes: out[m.group(1)].append(l)
    return out
ref = run([W + '/shellcheck', '-f', 'gcc'], 200)
vsc = run([W + '/vsc'], 2000)
bad = 0
for p in names:
    a, b = ref.get(p, []), vsc.get(p, [])
    if a != b:
        bad += 1
        print('==', p)
        sa, sb = set(a), set(b)
        for l in a:
            if l not in sb: print('  miss', l)
        for l in b:
            if l not in sa: print('  extra', l)
        if sa == sb: print('  (order/dup differs)')
print(f'{bad} of {n} files differ', file=sys.stderr)
