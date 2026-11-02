# More cases for cases.py: read errors (errno paths, run without capabilities so permissions
# apply), non-UTF-8 locales and file names, .shellcheckrc parse problems, path canonicalization.
# A case: (name, files, args, env, extra); extra: pre (shell commands run in the directory first),
# nocaps (run without root's capabilities), sh (a shell command, TOOL replaced by the binary),
# unset (environment variables to remove).
A = '#!/bin/sh\necho $1\n'
B = '#!/bin/sh\nx=1\n'
U = '#!/bin/sh\necho ’ $1\n'          # a unicode quote: SC1110 and non-ASCII in the excerpt
E = '#!/bin/sh\necho "é" $1\n'         # Latin-1-encodable
LIB = 'x=1\necho $1\n'
SRC = '#!/bin/bash\nsource ./lib.sh\necho "$x"\n'
import os
FORMATS = ['tty', 'gcc', 'json', 'json1', 'checkstyle', 'diff', 'quiet']

def more():
    c = []
    # ---- read errors
    c += [
        ('err_noperm', {'a.sh': A, 'b.sh': B}, ['a.sh', 'b.sh'], {}, {'pre': 'chmod 000 a.sh', 'nocaps': True}),
        ('err_noperm_dir', {'d/a.sh': A, 'b.sh': B}, ['d/a.sh', 'b.sh'], {}, {'pre': 'chmod 000 d', 'nocaps': True}),
        ('err_noperm_dir_x', {'d/a.sh': A, 'b.sh': B}, ['b.sh', 'd/a.sh'], {}, {'pre': 'chmod 600 d', 'nocaps': True}),
        ('err_eloop', {'b.sh': B}, ['loop', 'b.sh'], {}, {'pre': 'ln -s loop loop'}),
        ('err_dangling', {'b.sh': B}, ['dang', 'b.sh'], {}, {'pre': 'ln -s nowhere dang'}),
        ('err_toolong', {'b.sh': B}, ['x' * 300, 'b.sh'], {}),
        ('err_toolong_path', {'b.sh': B}, ['/'.join(['y' * 200] * 25), 'b.sh'], {}),
        ('err_notdir', {'b.sh': B}, ['b.sh/x.sh', 'b.sh'], {}),
        ('err_empty_name', {'b.sh': B}, ['', 'b.sh'], {}),
        ('err_dir_slash', {'d/a.sh': A}, ['d/', 'd/a.sh'], {}),
        ('err_dev_null', {}, ['/dev/null'], {}),
        ('err_dev_stdin', {'a.sh': A}, ['/dev/stdin'], {'STDIN': 'a.sh'}),
        ('err_fifo', {'b.sh': B}, ['p', 'b.sh'], {}, {'pre': 'mkfifo p', 'sh': 'cat b.sh > p 2>/dev/null & sleep 0.2; exec TOOL p b.sh'}),
        ('err_fifo_twice', {'a.sh': A}, ['p', 'p'], {}, {'pre': 'mkfifo p', 'sh': 'cat a.sh > p 2>/dev/null & sleep 0.2; exec TOOL p p'}),
        ('err_proc_self', {'a.sh': A}, ['/proc/self/fd/0'], {'STDIN': 'a.sh'}),
        ('err_src_noperm', {'lib.sh': LIB, 'a.sh': SRC}, ['-x', 'a.sh'], {}, {'pre': 'chmod 000 lib.sh', 'nocaps': True}),
        ('err_src_noperm_json', {'lib.sh': LIB, 'a.sh': SRC}, ['-x', '-f', 'json1', 'a.sh'], {}, {'pre': 'chmod 000 lib.sh', 'nocaps': True}),
        ('err_src_dir', {'lib.sh/x': '', 'a.sh': SRC}, ['-x', 'a.sh'], {}),
        ('err_src_loop', {'a.sh': SRC}, ['-x', 'a.sh'], {}, {'pre': 'ln -s lib.sh lib.sh'}),
        ('err_src_fifo', {'a.sh': '#!/bin/bash\nsource ./p\necho "$x"\n', 'lib.sh': LIB}, ['-x', 'a.sh'], {}, {'pre': 'mkfifo p', 'sh': 'cat lib.sh > p 2>/dev/null & sleep 0.2; exec TOOL -x a.sh'}),
        ('err_src_devstdin', {'a.sh': '#!/bin/bash\nsource /dev/stdin\necho "$x"\n', 'lib.sh': LIB}, ['-x', 'a.sh'], {'STDIN': 'lib.sh'}),
        ('err_src_stdin_input', {'a.sh': '#!/bin/bash\nsource /dev/stdin\necho "$x"\n', 'lib.sh': LIB}, ['a.sh', '/dev/stdin'], {'STDIN': 'lib.sh'}),
        ('err_rc_noperm', {'.shellcheckrc': 'disable=SC2086\n', 'a.sh': A, 'd/b.sh': A, 'c.sh': A}, ['a.sh', 'd/b.sh', 'c.sh', 'a.sh'], {}, {'pre': 'chmod 000 .shellcheckrc', 'nocaps': True}),
        ('err_rc_noperm_gcc', {'.shellcheckrc': 'disable=SC2086\n', 'a.sh': A}, ['-f', 'gcc', 'a.sh', 'nope.sh', 'a.sh'], {}, {'pre': 'chmod 000 .shellcheckrc', 'nocaps': True}),
        ('err_rc_is_dir', {'.shellcheckrc/x': '', 'shellcheckrc': 'disable=SC2086\n', 'a.sh': A}, ['a.sh'], {}),
        ('err_rc_dangling', {'shellcheckrc': 'disable=SC2086\n', 'a.sh': A}, ['a.sh'], {}, {'pre': 'ln -s nowhere .shellcheckrc'}),
        ('err_rcfile_noperm', {'rc': 'disable=SC2086\n', 'a.sh': A}, ['--rcfile', 'rc', 'a.sh', 'a.sh'], {}, {'pre': 'chmod 000 rc', 'nocaps': True}),
        ('err_rcfile_dir', {'rc/x': '', 'a.sh': A}, ['--rcfile', 'rc', 'a.sh'], {}),
        ('err_rcfile_missing_all_missing', {}, ['--rcfile', 'nope', 'x.sh', 'y.sh'], {}),
        ('err_rcfile_missing_after_missing', {'a.sh': A}, ['--rcfile', 'nope', 'x.sh', 'a.sh', 'a.sh'], {}),
        ('err_rcfile_missing_norc', {'a.sh': A}, ['--norc', '--rcfile', 'nope', 'a.sh'], {}),
        ('err_rc_cache', {'.shellcheckrc': 'disable=SC2086\n', 'a.sh': A, 'd/b.sh': A}, ['a.sh', 'd/nope.sh', 'a.sh', 'd/b.sh', 'a.sh'], {}, {'pre': 'chmod 000 .shellcheckrc', 'nocaps': True}),
        ('err_many_missing_order', {'a.sh': U * 300}, ['a.sh', 'n1', 'a.sh', 'n2', 'a.sh', 'a.sh', 'n3'], {}),
        ('err_many_missing_order_cs', {'a.sh': U * 300}, ['-f', 'checkstyle', 'a.sh', 'n1', 'a.sh', 'n2', 'a.sh', 'a.sh', 'n3'], {}),
        ('err_home_unset', {'a.sh': A}, ['a.sh'], {}, {'unset': ['HOME']}),
        ('err_home_empty', {'a.sh': A}, ['a.sh'], {'HOME': ''}),
        ('err_home_relative', {'h/.shellcheckrc': 'disable=SC2086\n', 'a.sh': A}, ['a.sh'], {'HOME': 'h'}),
        ('err_xdg_relative', {'x/shellcheckrc': 'disable=SC2086\n', 'a.sh': A}, ['a.sh'], {'XDG_CONFIG_HOME': 'x'}),
        ('err_xdg_empty', {'nohome/.config/shellcheckrc': 'disable=SC2086\n', 'a.sh': A}, ['a.sh'], {'XDG_CONFIG_HOME': ''}),
        ('err_home_noperm', {'nohome/.shellcheckrc': 'disable=SC2086\n', 'a.sh': A}, ['a.sh'], {}, {'pre': 'chmod 000 nohome/.shellcheckrc', 'nocaps': True}),
    ]
    # ---- locales and file names
    for loc in ['C', 'POSIX', 'C.UTF-8', 'en_US.ISO-8859-1']:
        tag = loc.replace('.', '_').replace('-', '')
        for f in FORMATS:
            c.append((f'loc_{tag}_{f}', {'u.sh': U, 'e.sh': E, 'a.sh': A}, ['-f', f, 'a.sh', 'u.sh', 'e.sh', 'a.sh'], {'LC_ALL': loc}))
        c += [
            (f'loc_{tag}_name', {'é.sh': A, 'a.sh': A}, ['a.sh', 'é.sh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_name_gcc', {'é.sh': A, 'a.sh': A}, ['-f', 'gcc', 'a.sh', 'é.sh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_name_json', {'é.sh': A, 'a.sh': A}, ['-f', 'json', 'a.sh', 'é.sh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_name_cs', {'é.sh': A, 'a.sh': A}, ['-f', 'checkstyle', 'a.sh', 'é.sh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_name_diff', {'é.sh': A, 'a.sh': A}, ['-f', 'diff', 'a.sh', 'é.sh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_bytename', {b'\xe9.sh': A, 'a.sh': A}, [b'\xe9.sh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_bytename_json', {b'\xe9.sh': A, 'a.sh': A}, ['-f', 'json1', 'a.sh', b'\xe9.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_bytename_cs', {b'\xe9.sh': A, 'a.sh': A}, ['-f', 'checkstyle', b'\xe9.sh', 'a.sh', b'\xe9no.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_missing_name', {'a.sh': A}, ['a.sh', 'éno.sh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_missing_name_cs', {'a.sh': A}, ['-f', 'checkstyle', 'a.sh', 'éno.sh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_footer', {'a.sh': '#!/bin/sh\né() { :; }\né\n', 'u.sh': U}, ['u.sh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_bad_shell', {'a.sh': A}, ['-s', 'ésh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_bad_format', {'a.sh': A}, ['-f', 'xé', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_bad_opt', {'a.sh': A}, ['--é', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_bad_num', {'a.sh': A}, ['-e', 'é', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_rcfile_name', {'a.sh': A}, ['--rcfile', 'é', 'a.sh', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_src_name', {'é.sh': LIB, 'a.sh': '#!/bin/bash\nsource ./é.sh\necho "$x"\n'}, ['-x', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_src_byte', {b'\xe9.sh': LIB, 'a.sh': b'#!/bin/bash\nsource ./\xe9.sh\necho "$x"\n'}, ['-x', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_src_missing', {'a.sh': '#!/bin/bash\nsource ./é.sh\necho "$x"\n'}, ['-x', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_surrogate', {'a.sh': b'#!/bin/sh\necho \xed\xa0\x80 $1\n'}, ['a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_surrogate_json', {'a.sh': b'#!/bin/sh\necho \xed\xa0\x80 $1\n'}, ['-f', 'json', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_overlong', {'a.sh': b'#!/bin/sh\necho \xc0\x80 \xc1\xbf \xe0\x80\x80 \xf4\x90\x80\x80 \xf8\x88\x80\x80\x80 $1\n'}, ['a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_overlong_json', {'a.sh': b'#!/bin/sh\necho \xc0\x80 \xc1\xbf \xe0\x80\x80 \xf4\x90\x80\x80 \xf8\x88\x80\x80\x80 $1\n'}, ['-f', 'json1', 'a.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_color', {'u.sh': U}, ['--color=always', 'u.sh', 'u.sh'], {'LC_ALL': loc}),
            (f'loc_{tag}_opts_env', {'a.sh': A}, ['a.sh'], {'LC_ALL': loc, 'SHELLCHECK_OPTS': '-s é'}),
        ]
    for env in [{'LANG': 'C'}, {'LANG': 'C.UTF-8', 'LC_CTYPE': 'C'}, {'LC_ALL': '', 'LC_CTYPE': 'POSIX'}, {'LANG': 'C', 'LC_ALL': 'xx'}, {'LC_CTYPE': 'C', 'LC_ALL': 'C.UTF-8'}, {'LANG': ''}, {}]:
        tag = '_'.join(k + '=' + v for k, v in env.items()).replace('.', '_') or 'none'
        c.append((f'locenv_{tag}', {'u.sh': U}, ['u.sh'], dict(env), {'unset': ['LANG', 'LC_ALL', 'LC_CTYPE']}))
    # ---- .shellcheckrc parse problems
    rcs = {
        'cr': 'disable=SC2086\r\n',
        'cr_only': '\r\n',
        'badutf8': b'# \xff\xfe comment\ndisable=SC2086\n',
        'badutf8_value': b'disable=SC2086\xff\n',
        'quoted': 'disable="SC2086"\n',
        'single_quoted': "disable='SC2086'\n",
        'open_quote': 'disable="SC2086\n',
        'unknown_key': 'frob=1\ndisable=SC2086\n',
        'unknown_value': 'shell=fish\n',
        'enable_unknown': 'enable=nope\n',
        'source_path': 'source-path=/nonexistent\n',
        'source': 'source=foo.sh\n',
        'comments': '# a\n  # b\n\tdisable=SC2086 # trailing\n# c',
        'tabs_spaces': ' \t disable=SC2086 \t \n',
        'no_newline': 'disable=SC2086',
        'two_on_line': 'disable=SC2086 disable=SC2034\n',
        'commas': 'disable=SC2086,SC2034,\n',
        'range': 'disable=SC2000-SC2100\n',
        'bad_range': 'disable=SC2100-SC2000\n',
        'lowercase': 'disable=sc2086\n',
        'spaces_eq': 'disable = SC2086\n',
        'shellcheck_prefix': '# shellcheck disable=SC2086\n',
        'shellcheck_prefix_bare': 'shellcheck disable=SC2086\n',
        'empty': '',
        'blank_lines': '\n\n\n',
        'bom': '﻿disable=SC2086\n',
        'nul': 'disable=SC2086\x00\n',
        'external_bad': 'external-sources=yes\n',
        'extended_bad': 'extended-analysis=1\n',
        'directive_only': 'disable\n',
        'equals_only': '=\n',
        'key_dash': '-disable=SC2086\n',
        'unicode_key': 'é=1\n',
        'long_error': 'disable=SC2086\n' * 50 + 'oops oops\n',
        'all': 'disable=all\n',
        'shell_dir': 'shell=bash\nshell=sh\n',
        'enable_disable': 'enable=all\ndisable=SC2250\n',
        'line_cont': 'disable=SC2086 \\\n SC2034\n',
    }
    for k, v in rcs.items():
        c.append((f'rcparse_{k}', {'.shellcheckrc': v, 'a.sh': '#!/bin/bash\nx=1\necho $1 $y\n[ $1 ]\n'}, ['a.sh'], {}))
        c.append((f'rcparse_{k}_json', {'.shellcheckrc': v, 'a.sh': '#!/bin/bash\nx=1\necho $1 $y\n[ $1 ]\n'}, ['-f', 'json1', 'a.sh'], {}))
    # ---- paths
    c += [
        ('path_dotdot', {'d/a.sh': A, 'd/.shellcheckrc': 'disable=SC2086\n', 'e/x': ''}, ['e/../d/a.sh'], {}),
        ('path_symlink_dir', {'real/a.sh': A, 'real/.shellcheckrc': 'disable=SC2086\n'}, ['link/a.sh'], {}, {'pre': 'ln -s real link'}),
        ('path_symlink_file', {'real/a.sh': A, 'real/.shellcheckrc': 'disable=SC2086\n', 'other/x': ''}, ['other/a.sh'], {}, {'pre': 'ln -s ../real/a.sh other/a.sh'}),
        ('path_symlink_dotdot', {'real/sub/x': '', 'a.sh': A, '.shellcheckrc': 'disable=SC2034\n'}, ['link/../a.sh'], {}, {'pre': 'ln -s real/sub link'}),
        ('path_missing_prefix_src', {'lib.sh': LIB, 'a.sh': '#!/bin/bash\nsource ./no/../lib.sh\necho "$x"\n'}, ['a.sh', 'lib.sh'], {}),
        ('path_src_symlink_input', {'lib.sh': LIB, 'a.sh': SRC}, ['a.sh', 'l2.sh'], {}, {'pre': 'ln -s lib.sh l2.sh'}),
        ('path_src_dotdot_input', {'d/lib.sh': LIB, 'd/a.sh': '#!/bin/bash\nsource ../d/lib.sh\necho "$x"\n'}, ['d/a.sh', 'd/./lib.sh'], {}),
        ('path_src_abs', {'lib.sh': LIB, 'a.sh': '#!/bin/bash\nsource @/lib.sh\necho "$x"\n'}, ['a.sh', 'lib.sh'], {}),
        ('path_scriptdir_relative', {'d/inc/lib.sh': LIB, 'd/a.sh': '#!/bin/bash\n# shellcheck source-path=SCRIPTDIR/inc\nsource lib.sh\necho "$x"\n'}, ['-x', 'd/a.sh'], {}),
        ('path_scriptdir_bare', {'lib.sh': LIB, 'a.sh': '#!/bin/bash\n# shellcheck source-path=SCRIPTDIR\nsource lib.sh\necho "$x"\n'}, ['-x', 'a.sh'], {}),
        ('path_scriptdir_dotdot', {'lib.sh': LIB, 'd/a.sh': '#!/bin/bash\n# shellcheck source-path=SCRIPTDIR/..\nsource lib.sh\necho "$x"\n'}, ['-x', 'd/a.sh'], {}),
        ('path_scriptdir_slashes', {'d/lib.sh': LIB, 'd/a.sh': '#!/bin/bash\n# shellcheck source-path=SCRIPTDIR//\nsource lib.sh\necho "$x"\n'}, ['-x', './/d//a.sh'], {}),
        ('path_scriptdir_source', {'d/lib.sh': LIB, 'd/a.sh': '#!/bin/bash\n# shellcheck source=SCRIPTDIR/lib.sh\nsource "$1"\necho "$x"\n'}, ['-x', 'd/a.sh'], {}),
        ('path_scriptdir_prefix', {'d/lib.sh': LIB, 'd/a.sh': '#!/bin/bash\n# shellcheck source-path=SCRIPTDIRX\nsource lib.sh\necho "$x"\n'}, ['-x', 'd/a.sh'], {}),
        ('path_P_scriptdir_abs', {'d/lib.sh': LIB, 'd/a.sh': '#!/bin/bash\nsource lib.sh\necho "$x"\n'}, ['-x', '-P', 'SCRIPTDIR', '@/d/a.sh'], {}),
        ('path_P_empty', {'lib.sh': LIB, 'd/a.sh': '#!/bin/bash\nsource lib.sh\necho "$x"\n'}, ['-x', '-P', ':', 'd/a.sh'], {}),
        ('path_rc_parent_symlink', {'top/.shellcheckrc': 'disable=SC2086\n', 'top/real/a.sh': A, 'other/x': ''}, ['other/l/a.sh'], {}, {'pre': 'ln -s ../top/real other/l'}),
        ('path_abs_input', {'a.sh': A, '.shellcheckrc': 'disable=SC2086\n'}, ['@/a.sh'], {}),
        ('path_trailing_dot', {'d/a.sh': A}, ['d/./a.sh', 'd/.'], {}),
        ('path_root_rc', {'a.sh': A}, ['/dev/null', 'a.sh'], {}),
        ('path_missing_rc_dir', {'.shellcheckrc': 'disable=SC2086\n'}, ['no/such/../../a.sh'], {}),
        ('path_diff_names', {'d/a.sh': A}, ['-f', 'diff', './d/a.sh', '@/d/a.sh', 'd//a.sh'], {}),
    ]
    # ---- command line
    c += [
        ('cli_jobs_bad', {'a.sh': A}, ['--jobs', 'x', 'a.sh'], {}),
        ('cli_jobs_after_dashdash', {'a.sh': A}, ['--', '--jobs', '2'], {}),
        ('cli_jobs_noarg', {'a.sh': A}, ['--jobs'], {}),
        ('cli_jobs_empty', {'a.sh': A}, ['--jobs=', 'a.sh'], {}),
        ('cli_jobs_as_arg', {'a.sh': A}, ['-f', '--jobs', 'a.sh'], {}),
        ('cli_jobs_prefix', {'a.sh': A}, ['--jo', '2', 'a.sh'], {}),
        ('cli_wiki_sc', {'a.sh': A, 'b.sh': B}, ['-W', 'SC', 'b.sh', 'a.sh'], {}),
        ('cli_wiki_sc_gcc', {'a.sh': A}, ['-W', 'SC', '-f', 'gcc', 'a.sh'], {}),
        ('cli_wiki_sc_missing', {}, ['-W', 'SC', 'nope.sh'], {}),
        ('cli_wiki_huge', {'a.sh': A}, ['-W', '18446744073709551615', 'a.sh'], {}),
        ('cli_wiki_wrap', {'a.sh': A, 'b.sh': B}, ['-W', '18446744073709551617', 'a.sh', 'b.sh'], {}),
        ('cli_exclude_sc', {'a.sh': A}, ['-e', 'SC', 'a.sh'], {}),
        ('cli_exclude_sc_clean', {'a.sh': '#!/bin/sh\necho "$1"\n'}, ['-e', 'SC', 'a.sh'], {}),
        ('cli_exclude_sc_later', {'a.sh': A}, ['-e', '2086,SC', 'a.sh'], {}),
        ('cli_include_sc', {'a.sh': A}, ['-i', 'SC,2086', 'a.sh'], {}),
        ('cli_include_sc_later', {'a.sh': A}, ['-i', '2086,SC', 'a.sh'], {}),
        ('cli_include_sc_severity', {'a.sh': A}, ['-S', 'error', '-i', 'SC', 'a.sh'], {}),
        ('cli_sc_many', {'a.sh': A}, ['-e', 'SCSCSC2086', 'a.sh'], {}),
        ('cli_opts_tabs', {'a.sh': A}, ['a.sh'], {'SHELLCHECK_OPTS': '-f\tgcc'}),
        ('cli_opts_only_spaces', {'a.sh': A}, ['a.sh'], {'SHELLCHECK_OPTS': '   '}),
        ('cli_opts_bad', {'a.sh': A}, ['a.sh'], {'SHELLCHECK_OPTS': '--frob'}),
        ('cli_home_slash', {'h/.shellcheckrc': 'disable=SC2086\n', 'f/a.sh': A}, [], {'HOME': '@/h/'}, {'sh': 'cd h && exec TOOL ../f/a.sh'}),
        ('cli_home_empty_cwd', {'w/.shellcheckrc': 'disable=SC2086\n', 'f/a.sh': A}, [], {'HOME': ''}, {'sh': 'cd w && exec TOOL ../f/a.sh'}),
        ('cli_xdg_trailing', {'x/shellcheckrc': 'disable=SC2086\n', 'f/a.sh': A}, [], {'XDG_CONFIG_HOME': '@/x//'}, {'sh': 'cd x && exec TOOL ../f/a.sh'}),
        # (with stdin closed, ShellCheck reads "-" from a descriptor of its own runtime and hangs)
        ('cli_stdin_dir', {'a.sh': A}, ['-', 'a.sh'], {}, {'sh': 'exec TOOL - a.sh < .'}),
        ('cli_stdout_full', {'a.sh': A}, ['a.sh'], {}, {'sh': 'exec TOOL a.sh > /dev/full'}),
        ('cli_stdout_full_json', {'a.sh': A}, ['-f', 'json', 'a.sh'], {}, {'sh': 'exec TOOL -f json a.sh > /dev/full'}),
        ('cli_stdout_full_version', {}, ['-V'], {}, {'sh': 'exec TOOL -V > /dev/full'}),
        ('cli_stderr_full', {}, ['nope.sh'], {}, {'sh': 'exec TOOL nope.sh 2> /dev/full'}),
        # (likewise with stdout closed: ShellCheck's writes go to its runtime's descriptor and it hangs)
    ]
    # ---- the data flow analysis's limit of 1,000,000 steps (ShellCheck takes about 3 minutes on
    # each): loops nested 340 deep need 994,319 steps, 341 deep over a million (SC_SLOW=1)
    if os.environ.get('SC_SLOW'):
        for n in (340, 341):
            c.append((f'dfa_nest{n}', {'a.sh': nest(n)}, ['-f', 'gcc', 'a.sh'], {}))
    return c

def nest(n):
    L = ['#!/bin/bash']
    for i in range(n): L.append(' ' * i + f'while [ "$v{i}" ]; do v{i}=$((v{i}+1)); x{i}=$v{(i+1)%n}')
    for i in reversed(range(n)): L.append(' ' * i + 'done')
    return '\n'.join(L) + '\n'
