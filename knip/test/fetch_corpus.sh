#!/bin/sh
# fetch_corpus.sh DIR: clones every project in corpus.txt into DIR/NAME at the commit recorded
# there, and installs its dependencies without running their scripts (as the parity runs did).
set -e
dir=${1:?usage: fetch_corpus.sh DIR}
list="$(cd "$(dirname "$0")" && pwd)/corpus.txt"
mkdir -p "$dir"
while read -r name url rev; do
  [ -n "$name" ] || continue
  if [ ! -d "$dir/$name" ]; then
    git init -q "$dir/$name"
    git -C "$dir/$name" remote add origin "$url"
  fi
  git -C "$dir/$name" fetch -q --depth 1 origin "$rev" 2>/dev/null || git -C "$dir/$name" fetch -q origin
  git -C "$dir/$name" checkout -q "$rev"
  (cd "$dir/$name" && CI=1 pnpm install --ignore-scripts --config.confirmModulesPurge=false > /dev/null 2>&1) || echo "install failed: $name"
done < "$list"
