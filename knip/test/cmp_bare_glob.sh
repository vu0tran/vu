#!/bin/bash
# Entry patterns ending in '**' ("scripts/**": every file below it, dotfiles too) against knip
# 6.44.1's output, saved in test/bare_glob (expected_N.txt for the Nth line of cases.txt; a line
# "DOTFILE ..." also makes scripts/.hidden.ts import src/b.ts).
#   VKNIP=path/to/vknip test/cmp_bare_glob.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
cd "$W"
mkdir -p packages/p/scripts/deep packages/p/scripts/.hid packages/p/src
printf '{"name":"root","private":true,"workspaces":["packages/*"]}\n' > package.json
printf '{"name":"p","version":"1.0.0"}\n' > packages/p/package.json
echo 'console.log(1)' > packages/p/scripts/indexnow-submit.mjs
echo 'export const a = 1' > packages/p/scripts/deep/x.ts
echo 'export const z = 1' > packages/p/scripts/z.ts
echo 'export const h = 1' > packages/p/scripts/.hidden.ts
echo 'export const d = 1' > packages/p/scripts/.hid/y.ts
echo 'x' > packages/p/scripts/notes.md
echo 'export const b = 1' > packages/p/src/b.ts
pass=0; fail=0; i=0
while IFS= read -r line; do
  i=$((i+1)); e=$line
  if [[ $line == DOTFILE* ]]; then e=${line#DOTFILE }; echo 'import "../src/b.ts";' > packages/p/scripts/.hidden.ts; fi
  printf '{"workspaces":{"packages/p":{"entry":%s,"project":["**/*.{js,mjs,ts}"]}}}\n' "$e" > knip.json
  got=$("$VKNIP" --no-progress 2>&1)
  if [ "$got" == "$(cat "$here/bare_glob/expected_$i.txt")" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL entry $line"; diff "$here/bare_glob/expected_$i.txt" <(echo "$got"); fi
  echo 'export const h = 1' > packages/p/scripts/.hidden.ts
done < "$here/bare_glob/cases.txt"
echo "cmp_bare_glob: $pass passed, $fail failed"
[ $fail -eq 0 ]
