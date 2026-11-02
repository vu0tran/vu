# cases.py SHELLCHECK VSC WORKDIR [NAME...]: command line, .shellcheckrc and source-following cases,
# each a small directory of files and an argument list; compares stdout, stderr and exit status.
import os, shutil, subprocess, sys

sc, vsc, work = sys.argv[1:4]
only = sys.argv[4:]

LIB = 'x=1\necho $1\n'
MAIN_SRC = '#!/bin/bash\nsource ./lib.sh\necho "$x"\n'
cases = [
    # name, files, args, env
    ('rc_disable', {'.shellcheckrc': 'disable=SC2086\n', 'a.sh': '#!/bin/sh\necho $1\n'}, ['a.sh'], {}),
    ('rc_disable_range', {'.shellcheckrc': 'disable=SC2000-SC2100\n', 'a.sh': '#!/bin/sh\necho $1\n`ls`\n'}, ['a.sh'], {}),
    ('rc_disable_all', {'.shellcheckrc': '# comment\ndisable=all\n', 'a.sh': 'echo $1\n'}, ['a.sh'], {}),
    ('rc_enable', {'.shellcheckrc': 'enable=require-variable-braces,quote-safe-variables\n', 'a.sh': '#!/bin/bash\nv=1\necho $v\n'}, ['a.sh'], {}),
    ('rc_enable_all', {'.shellcheckrc': 'enable=all\n', 'a.sh': '#!/bin/bash\nv=1\necho $v\n[ "$v" ]\ncase $v in a) ;; esac\nwhich ls\ncat f | grep x\n[ ! "$v" -eq 1 ]\necho $UNSET_X\n'}, ['a.sh'], {}),
    ('rc_shell', {'.shellcheckrc': 'shell=sh\n', 'a.sh': 'echo $1\n[[ x ]]\n'}, ['a.sh'], {}),
    ('rc_shell_bad', {'.shellcheckrc': 'shell=zsh\n', 'a.sh': 'echo $1\n'}, ['a.sh'], {}),
    ('rc_parse_error', {'.shellcheckrc': 'disable=SC2086\nfoo bar\n', 'a.sh': '#!/bin/sh\necho $1\n'}, ['a.sh'], {}),
    ('rc_parse_error2', {'.shellcheckrc': 'disable=\n', 'a.sh': '#!/bin/sh\necho $1\n'}, ['a.sh'], {}),
    ('rc_unknown_key', {'.shellcheckrc': 'frobnicate=1\ndisable=2086\n', 'a.sh': '#!/bin/sh\necho $1\n'}, ['a.sh'], {}),
    ('rc_parent', {'.shellcheckrc': 'disable=SC2086\n', 'sub/a.sh': '#!/bin/sh\necho $1\n'}, ['sub/a.sh'], {}),
    ('rc_nodot', {'shellcheckrc': 'disable=SC2086\n', 'a.sh': '#!/bin/sh\necho $1\n'}, ['a.sh'], {}),
    ('rc_norc', {'.shellcheckrc': 'disable=SC2086\n', 'a.sh': '#!/bin/sh\necho $1\n'}, ['--norc', 'a.sh'], {}),
    ('rc_rcfile', {'other': 'disable=SC2034\n', '.shellcheckrc': 'disable=SC2086\n', 'a.sh': '#!/bin/sh\necho $1\nx=1\n'}, ['--rcfile', 'other', 'a.sh'], {}),
    ('rc_rcfile_missing', {'a.sh': '#!/bin/sh\necho $1\n'}, ['--rcfile', 'nope', 'a.sh', 'a.sh'], {}),
    ('rc_extended_false', {'.shellcheckrc': 'extended-analysis=false\n', 'a.sh': '#!/bin/bash\nf() { :; }\nexit\necho hi\n'}, ['a.sh'], {}),
    ('rc_extended_bad', {'.shellcheckrc': 'extended-analysis=maybe\n', 'a.sh': '#!/bin/sh\necho $1\n'}, ['a.sh'], {}),
    ('rc_external', {'.shellcheckrc': 'external-sources=true\n', 'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['a.sh'], {}),
    ('rc_external_false', {'.shellcheckrc': 'external-sources=false\n', 'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['-x', 'a.sh'], {}),
    ('rc_source_path', {'.shellcheckrc': 'source-path=SCRIPTDIR/inc\nexternal-sources=true\n', 'inc/lib.sh': LIB, 'a.sh': '#!/bin/bash\nsource lib.sh\necho "$x"\n'}, ['a.sh'], {}),
    ('rc_home', {'home/.shellcheckrc': 'disable=SC2086\n', 'a.sh': '#!/bin/sh\necho $1\n'}, ['a.sh'], {'HOME': '@/home'}),
    ('rc_xdg', {'xdg/shellcheckrc': 'disable=SC2086\n', 'a.sh': '#!/bin/sh\necho $1\n'}, ['a.sh'], {'HOME': '@/nohome', 'XDG_CONFIG_HOME': '@/xdg'}),
    ('src_no_x', {'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['a.sh'], {}),
    ('src_x', {'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['-x', 'a.sh'], {}),
    ('src_x_a', {'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['-x', '-a', 'a.sh'], {}),
    ('src_x_a_json1', {'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['-x', '-a', '-f', 'json1', 'a.sh'], {}),
    ('src_x_a_json', {'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['-x', '-a', '-f', 'json', 'a.sh'], {}),
    ('src_x_a_gcc', {'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['-x', '-a', '-f', 'gcc', 'a.sh'], {}),
    ('src_x_a_checkstyle', {'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['-x', '-a', '-f', 'checkstyle', 'a.sh'], {}),
    ('src_x_a_diff', {'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['-x', '-a', '-f', 'diff', 'a.sh'], {}),
    ('src_both_inputs', {'lib.sh': LIB, 'a.sh': MAIN_SRC}, ['a.sh', 'lib.sh'], {}),
    ('src_missing', {'a.sh': MAIN_SRC}, ['-x', 'a.sh'], {}),
    ('src_nonconst', {'a.sh': '#!/bin/bash\nsource "$1"\n. $HOME/x\n'}, ['-x', 'a.sh'], {}),
    ('src_directive', {'lib.sh': LIB, 'a.sh': '#!/bin/bash\n# shellcheck source=lib.sh\nsource "$1"\necho "$x"\n'}, ['-x', 'a.sh'], {}),
    ('src_devnull', {'a.sh': '#!/bin/bash\n# shellcheck source=/dev/null\nsource "$1"\nsource /dev/null\necho "$y"\n'}, ['a.sh'], {}),
    ('src_recursive', {'lib.sh': 'source ./lib.sh\nz=1\n', 'a.sh': '#!/bin/bash\nsource ./lib.sh\necho "$z"\n'}, ['-x', '-a', 'a.sh'], {}),
    ('src_parse_fail', {'lib.sh': 'if then fi\n', 'a.sh': MAIN_SRC}, ['-x', 'a.sh'], {}),
    ('src_parse_fail_a', {'lib.sh': 'if then fi\n', 'a.sh': MAIN_SRC}, ['-x', '-a', 'a.sh'], {}),
    ('src_P', {'inc/lib.sh': LIB, 'a.sh': '#!/bin/bash\nsource lib.sh\necho "$x"\n'}, ['-x', '-P', 'inc', 'a.sh'], {}),
    ('src_P_scriptdir', {'d/inc/lib.sh': LIB, 'd/a.sh': '#!/bin/bash\nsource lib.sh\necho "$x"\n'}, ['-x', '-P', 'SCRIPTDIR/inc', 'd/a.sh'], {}),
    ('src_annot_path', {'inc/lib.sh': LIB, 'a.sh': '#!/bin/bash\n# shellcheck source-path=inc\nsource lib.sh\necho "$x"\n'}, ['-x', 'a.sh'], {}),
    ('src_dynamic_prefix', {'lib.sh': LIB, 'a.sh': '#!/bin/bash\nsource "$DIR/lib.sh"\necho "$x"\n'}, ['-x', 'a.sh'], {}),
    ('src_tilde', {'a.sh': '#!/bin/bash\nsource ~/lib.sh\n'}, ['-x', 'a.sh'], {}),
    ('src_external_directive', {'lib.sh': LIB, 'a.sh': '#!/bin/bash\n# shellcheck external-sources=true\nsource ./lib.sh\n'}, ['a.sh'], {}),
    ('src_lib_disable', {'lib.sh': '# shellcheck disable=SC2034\nx=1\necho $2\n', 'a.sh': MAIN_SRC}, ['-x', '-a', 'a.sh'], {}),
    ('src_tty_tabs', {'lib.sh': 'x=1\n\techo $1\n', 'a.sh': MAIN_SRC}, ['-x', '-a', 'a.sh'], {}),
    ('dir_disable', {'a.sh': '#!/bin/sh\n# shellcheck disable=SC2086,SC2034\necho $1\nx=1\n'}, ['a.sh'], {}),
    ('dir_enable_inline', {'a.sh': '#!/bin/bash\n# shellcheck enable=require-variable-braces\nv=1\necho "$v"\n'}, ['a.sh'], {}),
    ('dir_shell', {'a.sh': '# shellcheck shell=dash\necho $1\nlocal x\n'}, ['a.sh'], {}),
    ('dir_bad', {'a.sh': '#!/bin/sh\n# shellcheck disable=foo\necho $1\n# shellcheck frob=1\necho $2\n'}, ['a.sh'], {}),
    ('dir_quoted', {'a.sh': '#!/bin/sh\n# shellcheck disable="SC2086"\necho $1\n'}, ['a.sh'], {}),
    ('dir_extended', {'a.sh': '#!/bin/bash\n# shellcheck extended-analysis=false\nexit\necho hi\n'}, ['a.sh'], {}),
    ('flag_shell', {'a.sh': '#!/bin/bash\necho $1\n[[ x ]]\n'}, ['-s', 'sh', 'a.sh'], {}),
    ('flag_shell_python', {'a.sh': '#!/usr/bin/python\nprint(1)\n'}, ['-s', 'bash', 'a.sh'], {}),
    ('flag_severity', {'a.sh': '#!/bin/sh\necho $1\nx=1\n`ls`\n'}, ['-S', 'warning', 'a.sh'], {}),
    ('flag_include', {'a.sh': '#!/bin/sh\necho $1\nx=1\n`ls`\n'}, ['-i', 'SC2034,2006', 'a.sh'], {}),
    ('flag_exclude', {'a.sh': '#!/bin/sh\necho $1\nx=1\n`ls`\n'}, ['-e', 'SC2034', '-e', '2006', 'a.sh'], {}),
    ('flag_extended', {'a.sh': '#!/bin/bash\nexit\necho hi\n'}, ['--extended-analysis=false', 'a.sh'], {}),
    ('flag_enable', {'a.sh': '#!/bin/bash\nv=1\necho $v\n'}, ['-o', 'all', 'a.sh'], {}),
    ('flag_enable_list', {'a.sh': '#!/bin/bash\nv=1\necho $v\ncase $v in a) ;; esac\n'}, ['--enable=add-default-case,quote-safe-variables', 'a.sh'], {}),
    ('flag_wiki', {'a.sh': '#!/bin/sh\necho $1\nx=1\n`ls`\n'}, ['-W', '1', 'a.sh'], {}),
    ('flag_wiki0', {'a.sh': '#!/bin/sh\necho $1\nx=1\n`ls`\n'}, ['-W0', 'a.sh'], {}),
    ('flag_color', {'a.sh': '#!/bin/sh\necho $1\nx=1\n`ls`\n'}, ['--color=always', 'a.sh'], {}),
    ('flag_color_diff', {'a.sh': '#!/bin/sh\necho $1\n'}, ['-Calways', '-f', 'diff', 'a.sh'], {}),
    ('env_opts', {'a.sh': '#!/bin/sh\necho $1\nx=1\n'}, ['a.sh'], {'SHELLCHECK_OPTS': ' -e  SC2034 -f gcc'}),
    ('stdin', {'a.sh': '#!/bin/sh\necho $1\n'}, ['-'], {'STDIN': 'a.sh'}),
    ('stdin_twice', {'a.sh': '#!/bin/sh\necho $1\n'}, ['-', '-f', 'gcc', '-'], {'STDIN': 'a.sh'}),
    ('missing_file', {}, ['nope.sh'], {}),
    ('missing_file_json', {}, ['-f', 'json', 'nope.sh'], {}),
    ('missing_file_checkstyle', {}, ['-f', 'checkstyle', 'nope.sh'], {}),
    ('dir_input', {'d/x': ''}, ['d'], {}),
    ('double_dash', {'-a.sh': '#!/bin/sh\necho $1\n'}, ['--', '-a.sh'], {}),
    ('bom', {'a.sh': '﻿#!/bin/sh\necho $1\n'}, ['a.sh'], {}),
    ('crlf', {'a.sh': '#!/bin/sh\r\necho $1\r\n'}, ['a.sh'], {}),
    ('latin1', {'a.sh': b'#!/bin/sh\necho \xe9 $1\n'}, ['a.sh'], {}),
    ('utf8', {'a.sh': '#!/bin/sh\necho "é" $1 “hi”\n'}, ['a.sh'], {}),
    ('tabs', {'a.sh': '#!/bin/sh\n\techo\t$1\t$2\n'}, ['a.sh'], {}),
    ('no_trailing_nl_diff', {'a.sh': '#!/bin/sh\necho $1'}, ['-f', 'diff', 'a.sh'], {}),
    ('multiline_fix', {'a.sh': '#!/bin/sh\necho "$(\n  ls\n)" `\nls\n`\n'}, ['-f', 'diff', 'a.sh'], {}),
]

def run(cmd, d, env, stdin):
    e = dict(os.environ)
    e.pop('SHELLCHECK_OPTS', None)
    e['HOME'] = os.path.join(d, 'nohome')
    for k, v in env.items():
        if k != 'STDIN': e[k] = v.replace('@', d)
    inp = open(os.path.join(d, stdin), 'rb').read() if stdin else b''
    p = subprocess.run(cmd, cwd=d, env=e, input=inp, capture_output=True, timeout=60)
    return p.stdout, p.stderr, p.returncode

ok = bad = 0
for name, files, args, env in cases:
    if only and name not in only: continue
    d = os.path.join(work, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for f, c in files.items():
        p = os.path.join(d, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(c if isinstance(c, bytes) else c.encode())
    r1 = run([sc] + args, d, env, env.get('STDIN'))
    r2 = run([vsc] + args, d, env, env.get('STDIN'))
    if r1 == r2: ok += 1
    else:
        bad += 1
        print(f'--- DIFF {name} (exit {r1[2]} {r2[2]})')
        for i, what in ((0, 'stdout'), (1, 'stderr')):
            if r1[i] != r2[i]:
                print(f'  {what} shellcheck:'); print('    ' + r1[i].decode(errors='replace').replace('\n', '\n    ')[:1500])
                print(f'  {what} vsc:'); print('    ' + r2[i].decode(errors='replace').replace('\n', '\n    ')[:1500])
print(f'{ok} same, {bad} differ')
