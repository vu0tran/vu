#!/bin/zsh
# exact.sh VLINT [DIR]: the caches are exact. On a small project (in DIR), after each edit (add,
# remove, rename and move files, change the tsconfig, its extends base and paths, add a package
# and change its types, corrupt the caches), vlint warm (vtsc cache + --cache, twice) must print
# what a cold run prints. Prints EXACT_PASS or EXACT_FAIL; "cold changed" shows an edit mattered.
# The caches compare each path's stat with its ctime (lcache.stat_any), which utime can't set: an
# edit that keeps the size and puts the mtime back is caught. One that kept the ctime too (the
# clock set back, a file system snapshot restored) wouldn't be: that's the limit.
V=$1; W=${2:-${TMPDIR:-/tmp}/vlint-exact}; rm -rf $W; mkdir -p $W/proj/src $W/proj/extra
P=$W/proj; LIB=$HOME/.cache/vlint-parity/tslib
mkx() { rm -rf $1; mkdir -p $1/vlint; cp -R $LIB $1/vlint/tslib-b82676463eea69ca; }
mkx $W/xw; mkdir -p $W/cw
cat > $P/.oxlintrc.json <<'J'
{"categories": {"correctness": "off"}, "options": {"typeAware": true}, "rules": {"typescript/no-unsafe-assignment": "error","typescript/no-unsafe-member-access": "error","typescript/no-unsafe-call": "error","typescript/no-unsafe-argument": "error","typescript/no-unsafe-return": "error"}}
J
echo '{"compilerOptions": {"strict": true}, "include": ["src"]}' > $P/tsconfig.json
printf 'import { v } from "pkg";\nimport { h } from "al";\nexport const x: number = v;\nexport const hh: number = h;\nexport const gg: number = G;\n' > $P/src/a.ts
printf 'declare const q: any;\nexport const r: string = q;\n' > $P/src/b.ts
printf 'declare var G: any;\n' > $P/extra/e.ts
echo 'export declare const h: any;' > $P/extra/al_any.ts; echo 'export declare const h: number;' > $P/extra/al_num.ts
n=0; fail=0; prev=""
step() {
  n=$((n+1)); cd $P
  # (past the tsconfig cache's 2 s racy window: the warm run finds the last step's entries changed)
  sleep 2.2
  mkx $W/xc; rm -rf $W/cc; mkdir -p $W/cc
  XDG_CACHE_HOME=$W/xc $V --cache --cache-location $W/cc/ -f unix > $W/cold.$n 2>$W/cold.$n.err
  VLINT_TSCONFIG_DEBUG=1 XDG_CACHE_HOME=$W/xw $V --cache --cache-location $W/cw/ -f unix > $W/warm.$n 2>$W/warm.$n.err
  VLINT_TSCONFIG_DEBUG=1 XDG_CACHE_HOME=$W/xw $V --cache --cache-location $W/cw/ -f unix > $W/warm2.$n 2>$W/warm2.$n.err
  r=same; cmp -s $W/cold.$n $W/warm.$n || { r=DIFF; fail=1; }
  r2=same; cmp -s $W/cold.$n $W/warm2.$n || { r2=DIFF; fail=1; }
  ch=changed; [ -n "$prev" ] && cmp -s $prev $W/cold.$n && ch=UNCHANGED
  tc() { grep -ac "tsconfig .*: $1" $2; }
  echo "$n $1: $(wc -l < $W/cold.$n) lines, cold $ch; warm $r (tsconfigs changed $(tc changed $W/warm.$n.err), cached $(tc 'from the cache' $W/warm.$n.err)), warm again $r2 (cached $(tc 'from the cache' $W/warm2.$n.err))"
  prev=$W/cold.$n
}
step "start"
printf 'declare const z: any;\nexport const w: number = z.k;\n' > $P/src/c.ts; step "add a file"
mkdir -p $P/src/sub; printf 'declare const s: any;\nexport const t: number = s();\n' > $P/src/sub/s.ts; step "add a file in a new folder"
mkdir -p $P/src/sub/in; printf 'declare const i1: any;\nexport const j1: number = i1.k;\n' > $P/src/sub/in/i1.ts; step "add a folder two deep"
# (only src/sub/in's names change: src/sub's and src/'s mtimes stay)
printf 'declare const i2: any;\nexport const j2: number = i2.k;\n' > $P/src/sub/in/i2.ts; step "add a file two folders deep"
# (same size, mtime put back: only the ctime and the contents tell)
python3 -I -c "import os,sys;p=sys.argv[1];st=os.stat(p);b=open(p,'rb').read();n=b.replace(b'const s: any;',b'const s: {} ;');assert len(n)==len(b) and n!=b;open(p,'wb').write(n);os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns))" $P/src/sub/s.ts; step "edit a file, same size and mtime"
rm $P/src/b.ts; step "remove a file"
mv $P/src/c.ts $P/src/d.tsx; step "rename a file (.ts to .tsx)"
mv $P/src/d.tsx $P/src/sub/d.ts; step "move a file to another folder"
echo '{"compilerOptions": {"strict": true}, "include": ["src", "extra"]}' > $P/tsconfig.json; step "change the tsconfig (include)"
mkdir -p $P/node_modules/pkg; echo '{"name": "pkg", "version": "1.0.0", "types": "index.d.ts"}' > $P/node_modules/pkg/package.json
echo 'export declare const v: any;' > $P/node_modules/pkg/index.d.ts; step "add a package"
echo 'export declare const v: number;' > $P/node_modules/pkg/index.d.ts; step "change the package's types"
echo '{"name": "pkg", "version": "1.0.0", "types": "other.d.ts"}' > $P/node_modules/pkg/package.json; echo 'export declare const v: any;' > $P/node_modules/pkg/other.d.ts; step "change package.json types"
echo '{"compilerOptions": {"strict": true, "paths": {"al": ["./extra/al_any.ts"]}}, "include": ["src", "extra"]}' > $P/tsconfig.json; step "change a compiler option (paths)"
printf '{"extends": "./base.json", "include": ["src", "extra"]}' > $P/tsconfig.json; echo '{"compilerOptions": {"strict": true, "paths": {"al": ["./extra/al_num.ts"]}}}' > $P/base.json; step "tsconfig extends a base"
echo '{"compilerOptions": {"strict": true, "paths": {"al": ["./extra/al_any.ts"]}}}' > $P/base.json; step "change the base"
# corrupt caches: every cache file cut in half
for f in $(find $W/xw/vlint/vtsc-files $W/xw/vlint/tsconfig $W/cw -type f 2>/dev/null); do python3 -I -c "import sys;p=sys.argv[1];b=open(p,'rb').read();open(p,'wb').write(b[:len(b)//2])" $f; done; step "corrupt caches (halved)"
for f in $(find $W/xw/vlint/vtsc-files $W/xw/vlint/tsconfig $W/cw -type f 2>/dev/null); do : > $f; done; step "empty caches"
[ $fail = 0 ] && echo EXACT_PASS || echo EXACT_FAIL
rm -rf $W
