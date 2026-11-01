#!/bin/bash
# golangci-lint findings for every corpus repo, into $S/golint/want/REPO.txt
. /tmp/claude-0/-home-claude/dea9c188-f605-533c-be07-4172ff14c99d/scratchpad/golint/env.sh
mkdir -p $S/golint/want
for d in ${@:-$(ls $S/gocorpus)}; do
  (cd $S/gocorpus/$d && golangci-lint run --config $S/golint/golangci.yml --max-issues-per-linter 0 --max-same-issues 0 --output.text.print-issued-lines=false ./... > $S/golint/want/$d.txt 2> $S/golint/want/$d.err)
  echo "$d $(wc -l < $S/golint/want/$d.txt)"
done
echo BASELINE DONE
