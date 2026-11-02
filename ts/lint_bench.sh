#!/bin/sh
# vlint vs oxlint, Biome, ESLint on one corpus: bench.sh DIR TARGET   (user CPU and wall, min of N)
cd $1; T=$2
B=/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/tsbench/node_modules/@biomejs/cli-linux-x64/biome
OX="/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/tsbench/node_modules/.bin/oxlint -c /tmp/oxempty.json --disable-nested-config"
echo "corpus $1/$T: $(find $T -type f \( -name '*.ts' -o -name '*.js' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.mts' -o -name '*.cts' -o -name '*.tsx' -o -name '*.jsx' \) | wc -l) files"
uptime
for r in 1 2; do
echo "vlint 1 thread:   $(python3 /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/lint/bt.py 5 /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/vlint --jobs 1 $T)"
echo "oxlint 1 thread:  $(python3 /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/lint/bt.py 5 $OX --threads 1 $T)"
echo "vlint all cores:  $(python3 /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/lint/bt.py 5 /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/vlint $T)"
echo "oxlint all cores: $(python3 /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/lint/bt.py 5 $OX $T)"
done
echo "biome all cores:  $(python3 /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/lint/bt.py 3 $B lint --config-path=/tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/biomebench --max-diagnostics=0 $T)"
echo "eslint 1 thread:  $(python3 /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/lint/bt.py 1 /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/eslintbench/node_modules/.bin/eslint -c /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/eslintbench/eslint.config.mjs --no-config-lookup $T)"
uptime
