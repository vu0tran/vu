#!/bin/bash
# xp_native_test.sh VLINT A11Y_DIR COMMENTS_DIR: eslint-plugin-jsx-a11y's and eslint-comments' rules
# that vlint runs natively when a configuration loads them in jsPlugins (ljs.try_defer, rxa11y.vu,
# rxcomments.vu). A11Y_DIR is an installed eslint-plugin-jsx-a11y 6.10.2, COMMENTS_DIR an installed
# @eslint-community/eslint-plugin-eslint-comments 4.7.2 (their package folders, with their
# dependencies resolvable from there). Each case is a folder made in a temporary directory, linted
# with a `node` wrapper first on PATH that counts the plugin host's processes, natively and with
# VLINT_NATIVE_JS_PLUGINS=0 (everything in node): the two outputs must be the same. Prints one line
# a case and "xp_native: N failed".
set -u
VL=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
A11Y=$2
EC=$3
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

# mk CASE: a folder with both plugins installed (FAKE=version: a fake eslint-plugin-jsx-a11y of that
# version, with a control-has-associated-label and a foo that report every opening element) and the
# configuration on stdin
mk() {
  local d=$tmp/$1
  mkdir -p "$d/node_modules/@eslint-community"
  if [ -n "${FAKE:-}" ]; then
    mkdir -p "$d/node_modules/eslint-plugin-jsx-a11y"
    printf '{"name":"eslint-plugin-jsx-a11y","version":"%s","main":"index.js"}\n' "$FAKE" > "$d/node_modules/eslint-plugin-jsx-a11y/package.json"
    cat > "$d/node_modules/eslint-plugin-jsx-a11y/index.js" <<'EOF'
const mk = (m) => ({ meta: { type: "problem" }, create(context) { return { JSXOpeningElement(n) { context.report({ node: n, message: m }); } }; } });
module.exports = { rules: { "control-has-associated-label": mk("fake JS label"), foo: mk("fake JS foo") } };
EOF
  else
    ln -s "$A11Y" "$d/node_modules/eslint-plugin-jsx-a11y"
  fi
  ln -s "$EC" "$d/node_modules/@eslint-community/eslint-plugin-eslint-comments"
  cat > "$d/.oxlintrc.json"
  cat > "$d/a.jsx" <<'EOF'

/* eslint-disable no-alert */
export const A = () => <div role="button" onClick={f} />;
// eslint-disable-next-line a11y-js/control-has-associated-label -- a description
export const B = () => <button onClick={f} />;
// oxlint-disable-next-line a11y-js/interactive-supports-focus
export const C = () => <span role="checkbox" onKeyDown={f} aria-checked />;
// eslint-disable-next-line a11y-js/no-onchange
export const D = () => <button>Save</button>;
export const E = () => <li onClick={f}><label>x</label></li>;
// eslint-disable-next-line jsx-a11y/control-has-associated-label
export const F = () => <button />;
export const G = () => <select onChange={f} />;
EOF
  printf '/* eslint-disable no-alert */\nalert(1)\n' > "$d/b.jsx"
}

# run CASE [ENV...]: lint the case's folder natively and in node; the outputs (unix) in
# $tmp/CASE.out and CASE.js, hosts started natively in $tmp/CASE.n
run() {
  local c=$1; shift
  rm -f "$tmp/hosts"
  (cd "$tmp/$c" && env PATH="$tmp/bin:$PATH" XDG_CACHE_HOME="$tmp/xdg" "$@" "$VL" -f ${FMT:-unix} --report-unused-disable-directives ${FILES:-a.jsx} > "$tmp/$c.out" 2>&1)
  if [ -f "$tmp/hosts" ]; then wc -l < "$tmp/hosts" | tr -d ' ' > "$tmp/$c.n"; else echo 0 > "$tmp/$c.n"; fi
  (cd "$tmp/$c" && env PATH="$tmp/bin:$PATH" XDG_CACHE_HOME="$tmp/xdg" "$@" VLINT_NATIVE_JS_PLUGINS=0 "$VL" -f ${FMT:-unix} --report-unused-disable-directives ${FILES:-a.jsx} > "$tmp/$c.js" 2>&1)
}

# check CASE WHAT HOSTS [GREP...]: the native output as node's, HOSTS hosts started natively (0, or
# + for at least one), each GREP found in the output
check() {
  local c=$1 what=$2 hosts=$3; shift 3
  local r=ok n
  n=$(cat "$tmp/$c.n")
  [ -n "${NOCMP:-}" ] || cmp -s <(sed -E 's/"start_time": [0-9.e-]+//' "$tmp/$c.out") <(sed -E 's/"start_time": [0-9.e-]+//' "$tmp/$c.js") || r=bad
  if [ "$hosts" = + ]; then [ "$n" -ge 1 ] || r=bad; else [ "$n" = "$hosts" ] || r=bad; fi
  for g in "$@"; do grep -q -- "$g" "$tmp/$c.out" || r=bad; done
  if [ $r = ok ]; then echo "$c: ok ($what; $n hosts)"; else echo "$c: FAILED ($what; $n hosts)"; diff "$tmp/$c.js" "$tmp/$c.out" | sed 's/^/    /' | head -20; sed 's/^/    /' "$tmp/$c.out" | head -20; fails=$((fails + 1)); fi
}

A11Y_RULES='"a11y-js/control-has-associated-label": "error", "a11y-js/interactive-supports-focus": "warn", "a11y-js/no-noninteractive-element-interactions": "error", "a11y-js/no-onchange": "error", "a11y-js/label-has-for": "warn"'
EC_RULES='"@eslint-community/eslint-comments/require-description": "error", "@eslint-community/eslint-comments/disable-enable-pair": "warn"'
HEAD='"plugins": [], "categories": {"correctness": "off"}, "jsPlugins": [{"name": "a11y-js", "specifier": "eslint-plugin-jsx-a11y"}, "@eslint-community/eslint-plugin-eslint-comments"]'

# 1. names (an alias, and eslint-comments without one), severities, eslint- and oxlint- directives
#    naming them, the unused ones (one names oxlint's own jsx-a11y rule); no node
mk native <<EOF
{ $HEAD, "rules": { $A11Y_RULES, $EC_RULES } }
EOF
run native
check native "aliased names, severities, directives, unused directives" 0 'a.jsx:3:24: A control must be associated with a text label. \[Error/a11y-js(control-has-associated-label)\]' 'Warning/@eslint-community/eslint-comments(disable-enable-pair)' 'a.jsx:8:1: Unused eslint-disable directive' 'a.jsx:11:1: Unused eslint-disable directive'

# 2. eslint-comments under an alias, a directive on the first line: the host's error, as it words it
FILES="a.jsx b.jsx" mk throw <<EOF
{ "plugins": [], "categories": {"correctness": "off"}, "jsPlugins": [{"name": "ec", "specifier": "@eslint-community/eslint-plugin-eslint-comments"}], "rules": { "ec/require-description": "error", "ec/no-use": "warn" } }
EOF
FMT=json FILES="a.jsx b.jsx" run throw
check throw "alias; column -1 on line 1 throws in the host" 0 'Error running JS plugin.' 'at Object.create (.*lib/rules/no-use.js:'

# 3. a rule vlint lacks (alt-text, no-static-element-interactions) and options it doesn't take
#    (tabbable) in node, the rest natively, in the host's order
mk mixed <<EOF
{ $HEAD, "rules": { $A11Y_RULES, $EC_RULES, "a11y-js/alt-text": "error", "a11y-js/no-static-element-interactions": "error", "a11y-js/interactive-supports-focus": ["error", {"tabbable": ["button"]}] } }
EOF
run mixed
check mixed "alt-text and options in node, the rest native" + "a.jsx:3:24: Elements with the 'button' interactive role must be tabbable." 'a11y-js(no-onchange)'

# 4. options {} run natively
mk emptyopts <<EOF
{ $HEAD, "rules": { "a11y-js/control-has-associated-label": ["error", {}], "@eslint-community/eslint-comments/require-description": ["error", {}] } }
EOF
run emptyopts
check emptyopts "options {}: native" 0 'a11y-js(control-has-associated-label)'

# 5. the opt-outs: everything, one plugin, the configuration's settings
mk optout <<EOF
{ $HEAD, "rules": { $A11Y_RULES, $EC_RULES } }
EOF
run optout VLINT_NATIVE_JS_PLUGINS=0
check optout "VLINT_NATIVE_JS_PLUGINS=0" + 'a11y-js(control-has-associated-label)'
run optout VLINT_NATIVE_JSX_A11Y=0
mv "$tmp/optout.n" "$tmp/optout_a.n"; mv "$tmp/optout.out" "$tmp/optout_a.out"; mv "$tmp/optout.js" "$tmp/optout_a.js"
check optout_a "VLINT_NATIVE_JSX_A11Y=0: jsx-a11y in node" + 'a11y-js(control-has-associated-label)'
mk ecoff <<EOF
{ "plugins": [], "categories": {"correctness": "off"}, "jsPlugins": [{"name": "a11y-js", "specifier": "eslint-plugin-jsx-a11y"}, "@eslint-community/eslint-plugin-eslint-comments"], "rules": { $EC_RULES } }
EOF
run ecoff VLINT_NATIVE_JSX_A11Y=0
check ecoff "VLINT_NATIVE_JSX_A11Y=0, only eslint-comments' rules on: jsx-a11y is an ordinary JS plugin, loaded" + 'eslint-comments(require-description)'
run ecoff VLINT_NATIVE_ESLINT_COMMENTS=0
mv "$tmp/ecoff.n" "$tmp/ecoff_e.n"; mv "$tmp/ecoff.out" "$tmp/ecoff_e.out"; mv "$tmp/ecoff.js" "$tmp/ecoff_e.js"
check ecoff_e "VLINT_NATIVE_ESLINT_COMMENTS=0: in node" + 'eslint-comments(require-description)'
for st in nativeJsPlugins nativeJsxA11y; do
  mk "set_$st" <<EOF
{ $HEAD, "settings": {"vlint": {"$st": false}}, "rules": { $A11Y_RULES } }
EOF
  run "set_$st"
  check "set_$st" "settings.vlint.$st false: in node" + 'a11y-js(control-has-associated-label)'
done
mk set_ec <<EOF
{ $HEAD, "settings": {"vlint": {"nativeEslintComments": false}}, "rules": { $EC_RULES } }
EOF
run set_ec
check set_ec "settings.vlint.nativeEslintComments false: in node" + 'eslint-comments(require-description)'
mk set_other <<EOF
{ $HEAD, "settings": {"vlint": {"nativeEslintComments": false}}, "rules": { $A11Y_RULES } }
EOF
run set_other
check set_other "settings.vlint.nativeEslintComments false, only jsx-a11y's rules on: eslint-comments loaded" + 'a11y-js(control-has-associated-label)'

# 6. another 6.x is loaded in node for its rule names (the native control-has-associated-label,
#    the fake foo from node); another major version stays in node
FAKE=6.9.0 mk v69 <<EOF
{ $HEAD, "rules": { "a11y-js/control-has-associated-label": "error", "a11y-js/foo": "error" } }
EOF
run v69
! grep -q 'fake JS label' "$tmp/v69.out" && r=ok || r=bad
[ $r = ok ] && NOCMP=1 check v69 "6.9.0: control-has-associated-label native, foo in node" + 'fake JS foo' 'A control must be associated with a text label.' || { echo "v69: FAILED (the fake label rule ran)"; fails=$((fails + 1)); }
FAKE=5.0.0 mk v5 <<EOF
{ $HEAD, "rules": { "a11y-js/control-has-associated-label": "error", "a11y-js/foo": "error" } }
EOF
run v5
check v5 "5.0.0: in node" + 'fake JS label' 'fake JS foo'

# 7. eslint-plugin-jsx-a11y without an alias: its name is reserved, as before
mk reserved <<EOF
{ "plugins": [], "categories": {"correctness": "off"}, "jsPlugins": ["eslint-plugin-jsx-a11y"], "rules": {} }
EOF
run reserved
check reserved "no alias: the reserved name's error" 0 "Plugin name 'jsx-a11y' is reserved"

echo "xp_native: $fails failed"
[ $fails = 0 ]
