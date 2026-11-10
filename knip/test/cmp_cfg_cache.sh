#!/bin/bash
# --cache and JavaScript configs (kcache.vu): a small project with a Playwright config loaded by
# Node.js, changed step by step; after each step vknip --cache must print what vknip without it
# prints, and say whether it loaded the configs again when it should (VKNIP_PHASES).
#   VKNIP=path/to/vknip test/cmp_cfg_cache.sh
set -u
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT
cd "$W"
mkdir -p e2e tests2 src
printf '{"name":"p","devDependencies":{"@playwright/test":"1"},"knip":{"entry":["src/index.ts"]}}\n' > package.json
printf 'import { dir } from "./pw.dir.ts";\nexport default { testDir: process.env.E2E_DIR || dir };\n' > playwright.config.ts
printf 'export const dir = "e2e";\n' > pw.dir.ts
printf 'export const a = 1;\n' > e2e/a.spec.ts
printf 'export const b = 1;\n' > tests2/b.spec.ts
printf 'export const c = 1;\n' > src/index.ts
pass=0; fail=0
step() {  # step NAME EXPECT(hit|load) [env...]
  local name=$1 want=$2; shift 2
  local ref got why
  ref=$(env "$@" "$VKNIP" --no-progress 2>&1)
  got=$(env "$@" VKNIP_PHASES=1 "$VKNIP" --cache --cache-location "$W/.c" --no-progress 2>&1)
  why=$(echo "$got" | grep '^vknip: configs loaded again' || true)
  got=$(echo "$got" | grep -v '^PHASE\|^vknip: configs')
  local was=hit; [ -n "$why" ] && was=load
  if [ "$got" == "$ref" ] && [ "$was" == "$want" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL $name (want $want, got $was: $why)"; diff <(echo "$ref") <(echo "$got") | head -8; fi
}
"$VKNIP" --cache --cache-location "$W/.c" --no-progress > /dev/null 2>&1   # (fills the cache)
step "same again" hit
step "an unrelated file changes" hit
printf 'export const d = 1;\n' > src/other.ts; step "a new source file" hit
printf 'export const dir = "tests2";\n' > pw.dir.ts; step "a file the config imports changes" load
step "and again" hit
step "an environment variable the config reads" load E2E_DIR=e2e
step "the same value again" hit E2E_DIR=e2e
step "back to unset" load
step "a variable the config doesn't read" hit SOME_OTHER=1
printf 'import { dir } from "./pw.dir.ts";\nlet extra = "";\ntry { extra = (await import("./pw.extra.ts")).dir; } catch {}\nexport default { testDir: extra || process.env.E2E_DIR || dir };\n' > playwright.config.ts
step "the config itself changes" load
printf 'export const dir = "e2e";\n' > pw.extra.ts; step "a module it looked for appears" load
rm pw.extra.ts; step "and goes" load
touch -d '2001-01-01' package-lock.json; step "a lockfile appears" load
step "and stays" hit
# (a copy of the project with the same files, times included, sharing the cache location)
cp -a "$W" "$W.copy"; trap 'rm -rf "$W" "$W.copy"' EXIT
# (the same size as 'export const dir = "tests2";' and the same time)
printf 'export const dir =    "e2e";\n' > "$W.copy/pw.dir.ts"; touch -r "$W/pw.dir.ts" "$W.copy/pw.dir.ts"
[ "$(wc -c < "$W/pw.dir.ts")" == "$(wc -c < "$W.copy/pw.dir.ts")" ] || echo "(test setup: the sizes differ)"
cd "$W.copy"; step "a copy of the project, a file changed but not its size or time" load; cd "$W"
ls "$W/.c" | grep -q '^vknip-deps-' && { fail=$((fail+1)); echo "FAIL the node processes' records were left behind"; }
grep -q "E2E_DIR=e2e\|\"e2e\"" "$W/.c"/vknip-configs-* 2>/dev/null && grep -o '"E2E_DIR":"[^"]*"' "$W/.c"/vknip-configs-* | grep -qv '"E2E_DIR":""\|"E2E_DIR":"[0-9a-f]\{32\}"' && { fail=$((fail+1)); echo "FAIL an environment value was kept as it is"; }
echo "cmp_cfg_cache: $pass passed, $fail failed"
[ $fail -eq 0 ]
