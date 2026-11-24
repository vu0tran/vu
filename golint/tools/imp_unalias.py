#!/usr/bin/env python3
# unalias.py MISM FILES...: drops the alias of imports whose alias is the package's name when that
# name isn't the one goimports assumes from the path (goimports puts it back)
import sys, re
m = dict(l.split() for l in open(sys.argv[1]))
n = 0
for f in sys.argv[2:]:
    s = open(f).read()
    def rep(mo):
        global n
        if m.get(mo[3]) == mo[2]:
            n += 1
            return mo[1] + '"' + mo[3] + '"'
        return mo[0]
    t = re.sub(r'(?m)^(\s+|import )(\w+) "([^"]+)"', rep, s)
    if t != s: open(f, 'w').write(t)
print("unaliased", n)
