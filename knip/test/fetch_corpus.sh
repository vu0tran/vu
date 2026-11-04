#!/bin/sh
# fetch_corpus.sh DIR [NAME...]: clones every project in corpus.txt (or the ones named) into DIR/NAME
# at the commit recorded there, and installs its dependencies without running their scripts (as the
# parity runs did). The framework apps name the folder knip runs in, a setup step (nuxt prepare,
# svelte-kit sync, react-router typegen, astro sync: "_" stands for a space) and how to install.
set -e
dir=${1:?usage: fetch_corpus.sh DIR [NAME...]}; shift
list="$(cd "$(dirname "$0")" && pwd)/corpus.txt"
mkdir -p "$dir"
grep -v '^#' "$list" | while read -r name url rev folder setup install; do
  [ -n "$name" ] || continue
  if [ $# -gt 0 ]; then case " $* " in *" $name "*) ;; *) continue ;; esac; fi
  d="$dir/$name"
  if [ ! -d "$d" ]; then
    git init -q "$d"
    git -C "$d" remote add origin "$url"
  fi
  git -C "$d" fetch -q --depth 1 origin "$rev" 2>/dev/null || git -C "$d" fetch -q origin
  git -C "$d" checkout -q "$rev"
  w="$d/${folder:-.}"
  case "$install" in
    folder) (cd "$w" && CI=1 pnpm install --ignore-workspace --ignore-scripts > /dev/null 2>&1) || echo "install failed: $name" ;;
    root) (cd "$d" && { CI=1 pnpm install --frozen-lockfile --ignore-scripts > /dev/null 2>&1 || CI=1 pnpm install --no-frozen-lockfile --ignore-scripts > /dev/null 2>&1; }) || echo "install failed: $name" ;;
    *) (cd "$d" && CI=1 pnpm install --ignore-scripts --config.confirmModulesPurge=false > /dev/null 2>&1) || echo "install failed: $name" ;;
  esac
  if [ -n "$setup" ] && [ "$setup" != "-" ]; then (cd "$w" && $(echo "$setup" | tr _ ' ') > /dev/null 2>&1) || echo "setup failed: $name"; fi
done
