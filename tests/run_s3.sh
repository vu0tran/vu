#!/bin/bash
# The s3 module: 120 random requests per run signed as botocore (the AWS SDK's signer) signs them,
# headers and presigned URLs; then put, get, exists, delete and presigned URLs against moto's S3,
# which checks signatures. Each part is skipped (and says so) without botocore, or moto and boto3.
# Plain and under the sanitizers.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
PY=${S3_PY:-python3}
work=$(mktemp -d)
pass=0; fail=0
python3 s3/model.py cases "$work/cases" "${SEED:-$RANDOM}"
for flags in "--release" "--san"; do
  if ! $PY -c 'import botocore' 2>/dev/null; then echo "signing skipped: no botocore"; break; fi
  if ! $VU build s3/main.vu $flags -o "$work/main" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build $flags"; cat "$work/err"; continue; fi
  if "$work/main" "$work/cases" > "$work/out" 2>"$work/err" && $PY s3/model.py check "$work/cases" < "$work/out" > "$work/res" && ! grep -q 'ERROR\|runtime error' "$work/err"; then
    pass=$((pass+1)); echo "ok    signing $flags ($(tail -1 "$work/res"))"
  else fail=$((fail+1)); echo "FAIL  signing $flags"; head -20 "$work/res"; head -5 "$work/err"; fi
done
for flags in "--release" "--san"; do
  if ! $PY -c 'import moto.server, boto3' 2>/dev/null; then echo "moto skipped: no moto[server] and boto3"; break; fi
  if ! $VU build s3/live.vu $flags -o "$work/live" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build live $flags"; cat "$work/err"; continue; fi
  if timeout 300 $PY s3/live.py "$work/live" > "$work/res" 2>&1; then pass=$((pass+1)); echo "ok    against moto $flags ($(tail -1 "$work/res"))"
  else fail=$((fail+1)); echo "FAIL  against moto $flags"; tail -20 "$work/res"; fi
done
rm -rf "$work"
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
