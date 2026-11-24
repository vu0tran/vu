#!/bin/bash
# gofmt_cmp.sh DIR: golangci-lint and vgolint on DIR (its .golangci.yml), text and JSON, diffed
S=${S:?set S to the scratch folder (golangci-lint127, gocmp/vgolint_fmt)}
cd "$1" || exit 1
export GOTOOLCHAIN=go1.27.3 GOPROXY=off GOWORK=off GOOS=linux GOARCH=amd64
GOLANGCI_LINT_CACHE=$(mktemp -d) $S/golangci-lint127 run --allow-parallel-runners ./... > /tmp/$$.g.txt 2>/tmp/$$.g.err; ge=$?
GOLANGCI_LINT_CACHE=$(mktemp -d) $S/golangci-lint127 run --allow-parallel-runners --output.json.path stdout ./... 2>/dev/null | head -1 | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d['Issues'],indent=0))" > /tmp/$$.g.json
VGOLINT_QUIET=1 $S/gocmp/vgolint_fmt run --no-cache ./... > /tmp/$$.v.txt 2>/tmp/$$.v.err; ve=$?
VGOLINT_QUIET=1 $S/gocmp/vgolint_fmt run --no-cache --output.json.path stdout ./... 2>/dev/null | head -1 | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d['Issues'],indent=0))" > /tmp/$$.v.json
echo "exit golangci=$ge vgolint=$ve; issues: $(grep -c 'File is not' /tmp/$$.g.txt) / $(grep -c 'File is not' /tmp/$$.v.txt)"
diff /tmp/$$.g.txt /tmp/$$.v.txt > /tmp/$$.d1 && echo "text same" || { echo "TEXT DIFF"; head -40 /tmp/$$.d1; }
diff /tmp/$$.g.json /tmp/$$.v.json > /tmp/$$.d2 && echo "json same" || { echo "JSON DIFF"; head -40 /tmp/$$.d2; }
rm -f /tmp/$$.*
