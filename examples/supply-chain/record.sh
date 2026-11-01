#!/bin/sh
# Records the supply-chain demo for real: the same compromised package (slugify 1.1.0, which sends
# GITHUB_TOKEN to an attacker's server) in Node and in Vu, then draws demo.gif. Needs vu, node,
# python3 with Pillow, and git. examples/supply-chain/record.sh
set -e
here=$(cd "$(dirname "$0")" && pwd); w=$(mktemp -d); trap 'rm -rf "$w"' EXIT
export GITHUB_TOKEN=ghp_demo_9f8e7d6c5b4a HOME="$w/home"; mkdir -p "$HOME"
g="git -c user.name=acme -c user.email=dev@acme.example -c init.defaultBranch=main -c advice.detachedHead=false"
# the package's repository, with 1.0.0 and the compromised 1.1.0, and a registry that lists both
mkdir -p "$w/src/slugify" && cd "$w/src/slugify" && $g init -q
cp "$here/vu/slugify-1.0.0.vu" slugify.vu && $g add -A && $g commit -qm 1.0.0 && $g tag v1.0.0
cp "$here/vu/slugify-1.1.0.vu" slugify.vu && $g add -A && $g commit -qm "1.1.0: faster" && $g tag v1.1.0
git clone -q "file://$w/src/slugify" "$w/dev" 2>/dev/null
{ echo "# demo registry"; vu publish slugify v1.0.0 "$w/dev" 2>/dev/null; vu publish slugify v1.1.0 "$w/dev" 2>/dev/null | grep '^version'; } > "$w/registry.txt"
export VU_REGISTRY="file://$w/registry.txt"
# Node: the app, with slugify 1.1.0 installed
mkdir -p "$w/node/node_modules/slugify"
cp "$here/node/main.js" "$here/node/package.json" "$w/node/"
cp "$here/node/slugify-1.1.0/"* "$w/node/node_modules/slugify/"
cd "$w/node"
tail -2 node_modules/slugify/index.js > "$w/out_node_cat.txt"
python3 "$here/listen.py" > "$w/stolen.txt" & sleep 0.5
node main.js > "$w/out_node.txt"; sleep 0.5; cat "$w/stolen.txt" >> "$w/out_node.txt"
# Vu: the same app and the same compromised version
mkdir -p "$w/vu" && cp "$here/vu/main.vu" "$w/vu/" && cd "$w/vu"
echo "need slugify v1.1.0" > vu.pkg
vu get main.vu >/dev/null 2>&1
tail -4 "$HOME/.cache/vu/pkg/slugify@v1.1.0/slugify.vu" > "$w/out_vu_cat.txt"
cat vu.pkg > "$w/out_vu_pkg.txt"
vu run main.vu > "$w/out_vu.txt" 2>&1 || true
sed -i "s#$HOME#~#g" "$w/out_vu.txt"
cd "$w" && python3 "$here/make_gif.py" "$here/demo.gif"
cat "$w/out_node.txt" "$w/out_vu.txt"
