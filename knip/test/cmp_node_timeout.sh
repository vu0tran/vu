#!/bin/bash
# A config that never finishes loading (it awaits a promise a timer keeps alive: node waits at 0% CPU)
# must not hang vknip: after VKNIP_NODE_TIMEOUT seconds it fails as a config that doesn't load, and no
# node process is left behind.
#   VKNIP=path/to/vknip test/cmp_node_timeout.sh
set -u
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
cd "$W"; mkdir src
printf '{"name":"h","version":"1.0.0","type":"module","devDependencies":{"vitest":"3.0.0"}}\n' > package.json
printf 'await new Promise(() => { setInterval(() => {}, 1000); });\nexport default { test: { include: ["src/**/*.test.ts"] } };\n' > vitest.config.ts
echo 'export const a = 1' > src/index.ts
s=$(date +%s)
out=$(VKNIP_NODE_TIMEOUT=3 timeout 60 "$VKNIP" --no-progress 2>&1); rc=$?
t=$(( $(date +%s) - s ))
fail=0
[ $rc -ne 124 ] || { echo "FAIL: still hung after 60 s"; fail=1; }
echo "$out" | grep -q "Error loading vitest.config.ts (vknip: node didn't finish loading this in 3 s" || { echo "FAIL: no error naming the config"; echo "$out"; fail=1; }
[ $t -le 20 ] || { echo "FAIL: took $t s"; fail=1; }
sleep 1; pgrep -f "vknip.*input-type=module|input-type=module.*$W" > /dev/null && { echo "FAIL: a node process was left"; fail=1; }
[ $fail -eq 0 ] && echo "cmp_node_timeout: passed ($t s)"
exit $fail
