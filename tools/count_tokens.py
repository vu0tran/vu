#!/usr/bin/env python3
"""Count LLM tokens in source files, fairly: strip comments, apply each language's
standard formatter, then count with the o200k (GPT-4o) tokenizer via gpt-tokenizer.

usage: count_tokens.py FILE...
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FORMATTERS = {'.c': ['clang-format'], '.cpp': ['clang-format'], '.rs': ['rustfmt', '--emit', 'stdout', '-q'],
              '.go': ['gofmt']}


def strip_comments(text, ext):
    if ext == '.vu':
        out = []
        for line in text.split('\n'):
            in_str = False
            for i, ch in enumerate(line):
                if ch == '"' and (i == 0 or line[i - 1] != '\\'):
                    in_str = not in_str
                elif ch == '#' and not in_str:
                    line = line[:i]
                    break
            if line.strip():
                out.append(line.rstrip())
        return '\n'.join(out) + '\n'
    # C-family: drop // and /* */ comments outside string and char literals
    pattern = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])\'|//[^\n]*|/\*.*?\*/', re.S)
    text = pattern.sub(lambda m: '' if m.group().startswith('/') else m.group(), text)
    return '\n'.join(l.rstrip() for l in text.split('\n') if l.strip()) + '\n'


def normalize(path):
    ext = os.path.splitext(path)[1]
    with open(path, encoding='utf-8') as f:
        text = strip_comments(f.read(), ext)
    if ext in FORMATTERS:
        with tempfile.NamedTemporaryFile('w', suffix=ext, delete=False) as tf:
            tf.write(text)
        cmd = FORMATTERS[ext] + [tf.name]
        r = subprocess.run(cmd, capture_output=True, text=True)
        os.unlink(tf.name)
        if r.returncode == 0 and r.stdout.strip():
            text = r.stdout
    return text


def main(paths):
    texts = {p: normalize(p) for p in paths}
    js = ("const {encode} = require('gpt-tokenizer');"
          "const t = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
          "const r = {}; for (const k in t) r[k] = encode(t[k]).length;"
          "console.log(JSON.stringify(r));")
    r = subprocess.run(['node', '-e', js], input=json.dumps(texts), capture_output=True, text=True, cwd=HERE)
    if r.returncode:
        sys.exit(r.stderr)
    counts = json.loads(r.stdout)
    for p in paths:
        lines = texts[p].count('\n')
        print(f'{os.path.basename(p):<18} {counts[p]:>6} tokens {lines:>5} lines')


if __name__ == '__main__':
    main(sys.argv[1:])
