#!/bin/zsh
# ref.sh: oxlint 1.94.0 + tsgolint 7.0.2008 (the target, installed in ~/.cache/vlint-parity/oxlatest)
# on the corpus ($VLINT_CORPUS), the reference tparity.sh compares with (~/.cache/vlint-parity/ref_ox194_unix.txt;
# paths relative to the corpus ($VLINT_CORPUS)). `ref.sh 179` runs the corpus's own pinned 1.79.0 + 7.0.2001
# into ref_ox_unix.txt instead. Needs a recent node.
J=${VLINT_CORPUS:?set VLINT_CORPUS to the folder linted (the root of a JS monorepo)}
D=$HOME/.cache/vlint-parity; mkdir -p $D
L=$D/oxlatest/node_modules
export PATH=/opt/homebrew/bin:$PATH
cd $J
if [ "$1" = 179 ]; then
  OXLINT_TSGOLINT_PATH=$J/node_modules/.pnpm/@oxlint-tsgolint+darwin-arm64@7.0.2001/node_modules/@oxlint-tsgolint/darwin-arm64/tsgolint \
    node_modules/.bin/oxlint --disable-nested-config -A typescript/no-misused-promises -f unix > $D/ref_ox_unix.raw 2> $D/ref_ox_err.txt
  grep -E '^[^ ].*:[0-9]+:[0-9]+: .*\]$' $D/ref_ox_unix.raw > $D/ref_ox_unix.txt
  wc -l $D/ref_ox_unix.txt
else
  OXLINT_TSGOLINT_PATH=$L/@oxlint-tsgolint/darwin-arm64/tsgolint \
    $L/.bin/oxlint --disable-nested-config -A typescript/no-misused-promises -f unix > $D/ref_ox194_unix.raw 2> $D/ref_ox194_err.txt
  grep -E '^[^ ].*:[0-9]+:[0-9]+: .*\]$' $D/ref_ox194_unix.raw > $D/ref_ox194_unix.txt
  wc -l $D/ref_ox194_unix.txt
fi
