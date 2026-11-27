#!/bin/bash
# rh_native_test.sh VLINT PLUGIN_DIR: eslint-plugin-react-hooks' compiler rules run on vlint's
# React Compiler (ljs.try_defer, rmore10.vu). PLUGIN_DIR is an installed eslint-plugin-react-hooks
# 7.1.1 (its package folder, with its dependencies resolvable from there). Each case is a folder
# made in a temporary directory, linted with a `node` wrapper first on PATH that counts the plugin
# host's processes. Prints one line a case and "rh_native: N failed".
set -u
VL=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
PLUG=$2
REAL_NODE=$(command -v node)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/bin" "$tmp/xdg"
cat > "$tmp/bin/node" <<EOF
#!/bin/sh
case "\$*" in *--version*) ;; *) echo x >> "$tmp/hosts" ;; esac
exec "$REAL_NODE" "\$@"
EOF
chmod +x "$tmp/bin/node"
fails=0

# a folder with the plugin installed (or a fake one: FAKE=version) and a config
mk() {
  local d=$tmp/$1
  mkdir -p "$d/node_modules"
  if [ -n "${FAKE:-}" ]; then
    mkdir -p "$d/node_modules/eslint-plugin-react-hooks"
    printf '{"name":"eslint-plugin-react-hooks","version":"%s","main":"index.js"}\n' "$FAKE" > "$d/node_modules/eslint-plugin-react-hooks/package.json"
    cat > "$d/node_modules/eslint-plugin-react-hooks/index.js" <<'EOF'
const mk = (m) => ({ meta: { type: "problem" }, create(context) { return { Program(n) { context.report({ node: n, message: m }); } }; } });
module.exports = { meta: { name: "eslint-plugin-react-hooks" }, rules: { purity: mk("fake JS purity"), foo: mk("fake JS foo") } };
EOF
  else
    ln -s "$PLUG" "$d/node_modules/eslint-plugin-react-hooks"
  fi
  cat > "$d/.oxlintrc.json"
  cat > "$d/a.tsx" <<'EOF'
import { useMemo, useRef, useState } from "react";

export function Clock() {
  const now = Date.now();
  // eslint-disable-next-line react-hooks-js/purity
  const r = Math.random();
  // oxlint-disable-next-line react-hooks-js/purity
  const p = performance.now();
  // eslint-disable-next-line react/purity
  const q = Math.random();
  return <div>{now}{r}{p}{q}</div>;
}

export function Refy() {
  const ref = useRef(0);
  const v = ref.current;
  return <div>{v}</div>;
}

export function Setter() {
  const [x, setX] = useState(0);
  // eslint-disable-next-line react-hooks-js/refs
  setX(1);
  return <div>{x}</div>;
}

export function Memo({ lead }: { lead?: { address?: string } }) {
  const a = useMemo(() => {
    if (typeof lead?.address === "string") return lead.address;
    return null;
  }, [lead?.address]);
  return <div>{a}</div>;
}

export function useCond(c: boolean) {
  if (c) {
    useState(0);
  }
}
EOF
}

# run CASE [ENV...]: lint the case's folder; the output (unix) in $tmp/CASE.out, hosts started in $tmp/CASE.n
run() {
  local c=$1; shift
  rm -f "$tmp/hosts"
  (cd "$tmp/$c" && env PATH="$tmp/bin:$PATH" XDG_CACHE_HOME="$tmp/xdg" "$@" "$VL" -f unix --report-unused-disable-directives a.tsx > "$tmp/$c.out" 2>&1)
  if [ -f "$tmp/hosts" ]; then wc -l < "$tmp/hosts" | tr -d ' ' > "$tmp/$c.n"; else echo 0 > "$tmp/$c.n"; fi
}

check() {
  local c=$1 what=$2
  if [ "$3" = ok ]; then echo "$c: ok ($what)"; else echo "$c: FAILED ($what)"; sed 's/^/    /' "$tmp/$c.out" | head -30; fails=$((fails + 1)); fi
}

RULES='"react-hooks-js/purity": "error", "react-hooks-js/refs": "warn", "react-hooks-js/set-state-in-render": "error"'
HEAD='"plugins": [], "categories": {"correctness": "off"}, "jsPlugins": [{"name": "react-hooks-js", "specifier": "eslint-plugin-react-hooks"}]'

# 1. the rules under the configuration's names, with its severities; the disable directives that name
#    them (eslint- and oxlint-), not the native react/purity; the unused one reported; no node
mk native <<EOF
{ $HEAD, "rules": { $RULES } }
EOF
run native
cat > "$tmp/native.exp" <<'EOF'
a.tsx:16:13: Cannot access refs during render [Warning/react-hooks-js(refs)]
a.tsx:4:15: Cannot call impure function during render [Error/react-hooks-js(purity)]
a.tsx:10:13: Cannot call impure function during render [Error/react-hooks-js(purity)]
a.tsx:23:3: Cannot call setState during render [Error/react-hooks-js(set-state-in-render)]
a.tsx:9:3: Unused eslint-disable directive (no problems were reported). [Warning]
a.tsx:22:3: Unused eslint-disable directive (no problems were reported). [Warning]

6 problems
EOF
cmp -s "$tmp/native.exp" "$tmp/native.out" && [ "$(cat "$tmp/native.n")" = 0 ] && r=ok || r=bad
check native "aliased names, severities, directives, unused directives, no node ($(cat "$tmp/native.n") hosts)" $r

# 2. the native react/purity at the same time: each reports under its own name, each name's directives apply to it
mk both <<EOF
{ $HEAD, "plugins": ["react"], "rules": { $RULES, "react/purity": "warn" } }
EOF
run both
n1=$(grep -c 'react-hooks-js(purity)' "$tmp/both.out"); n2=$(grep -c '\[Warning/react(purity)\]' "$tmp/both.out")
[ "$n1" = 2 ] && [ "$n2" = 1 ] && [ "$(cat "$tmp/both.n")" = 0 ] && r=ok || r=bad
check both "react-hooks-js(purity) $n1 (want 2), react(purity) $n2 (want 1: a directive naming any plugin's purity disables react/purity, as in oxlint)" $r

# 3. rules the port lacks (preserve-manual-memoization; rules-of-hooks, not a compiler rule) run in
#    node, the rest natively
mk lacks <<EOF
{ $HEAD, "rules": { $RULES, "react-hooks-js/preserve-manual-memoization": "error", "react-hooks-js/rules-of-hooks": "error" } }
EOF
run lacks
grep -q '^a.tsx:37:5: React Hook "useState" is called conditionally.*\[Error/react-hooks-js(rules-of-hooks)\]$' "$tmp/lacks.out" && grep -q '^a.tsx:4:15: Cannot call impure function during render \[Error/react-hooks-js(purity)\]$' "$tmp/lacks.out" && [ "$(cat "$tmp/lacks.n")" -ge 1 ] && r=ok || r=bad
check lacks "rules-of-hooks from node, purity native ($(cat "$tmp/lacks.n") hosts)" $r

# 4. VLINT_NATIVE_REACT_HOOKS=0: every rule in node (the plugin's own messages)
run native VLINT_NATIVE_REACT_HOOKS=0
mv "$tmp/native.out" "$tmp/optout.out"; mv "$tmp/native.n" "$tmp/optout.n"
grep -q '^a.tsx:4:15: Error: Cannot call impure function during render$' "$tmp/optout.out" && [ "$(cat "$tmp/optout.n")" -ge 1 ] && r=ok || r=bad
check optout "VLINT_NATIVE_REACT_HOOKS=0: in node ($(cat "$tmp/optout.n") hosts)" $r

# 5. settings.vlint.nativeReactHooks false: the same
mk settings <<EOF
{ $HEAD, "settings": {"vlint": {"nativeReactHooks": false}}, "rules": { $RULES } }
EOF
run settings
grep -q '^a.tsx:4:15: Error: Cannot call impure function during render$' "$tmp/settings.out" && [ "$(cat "$tmp/settings.n")" -ge 1 ] && r=ok || r=bad
check settings "settings.vlint.nativeReactHooks false: in node" $r

# 6. options other than {} keep that rule in node (here they turn purity off); {} doesn't
mk opts <<EOF
{ $HEAD, "rules": { $RULES, "react-hooks-js/purity": ["error", {"environment": {"validateNoImpureFunctionsInRender": false}}] } }
EOF
run opts
! grep -q 'react-hooks-js(purity)' "$tmp/opts.out" && grep -q '^a.tsx:16:13: Cannot access refs during render \[Warning/react-hooks-js(refs)\]$' "$tmp/opts.out" && [ "$(cat "$tmp/opts.n")" -ge 1 ] && r=ok || r=bad
check opts "options: purity in node (off by its options), refs native" $r
mk emptyopts <<EOF
{ $HEAD, "rules": { $RULES, "react-hooks-js/purity": ["error", {}] } }
EOF
run emptyopts
grep -q '^a.tsx:4:15: Cannot call impure function during render \[Error/react-hooks-js(purity)\]$' "$tmp/emptyopts.out" && [ "$(cat "$tmp/emptyopts.n")" = 0 ] && r=ok || r=bad
check emptyopts "options {}: native, no node" $r

# 7. another major version stays in node; another 7.x is loaded in node for its rule names, and
#    the rules the port has run natively
FAKE=6.1.0 mk v6 <<EOF
{ $HEAD, "rules": { "react-hooks-js/purity": "error", "react-hooks-js/foo": "error" } }
EOF
run v6
grep -q 'fake JS purity \[Error/react-hooks-js(purity)\]' "$tmp/v6.out" && grep -q 'fake JS foo' "$tmp/v6.out" && r=ok || r=bad
check v6 "6.1.0: in node" $r
FAKE=7.2.0 mk v72 <<EOF
{ $HEAD, "rules": { "react-hooks-js/purity": "error", "react-hooks-js/foo": "error" } }
EOF
run v72
! grep -q 'fake JS purity' "$tmp/v72.out" && grep -q '^a.tsx:4:15: Cannot call impure function during render \[Error/react-hooks-js(purity)\]$' "$tmp/v72.out" && grep -q 'fake JS foo' "$tmp/v72.out" && r=ok || r=bad
check v72 "7.2.0: purity native, foo in node" $r

echo "rh_native: $fails failed"
[ $fails = 0 ]
