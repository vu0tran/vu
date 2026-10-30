#!/bin/bash
# The mail module: SMTP with STARTTLS and sign-in, TLS from the start, a local relay, refusals (a wrong
# password, a remote server without STARTTLS, header injection, a server that answers STARTTLS with
# more than its 220) against aiosmtpd, and Resend's API against a fake one; the messages are read
# with Python's email package. Skipped (and says so) without aiosmtpd. Plain and under the sanitizers.
cd "$(dirname "$0")" || exit 1
VU=${VU:-"$PWD/../vu"}
PY=${MAIL_PY:-python3}
if ! $PY -c 'import aiosmtpd' 2>/dev/null; then echo "0 passed, 0 failed (skipped: no aiosmtpd)"; exit 0; fi
work=$(mktemp -d)
pass=0; fail=0
for flags in "--release" "--san"; do
  if ! $VU build mail/main.vu $flags -o "$work/main" 2>"$work/err"; then fail=$((fail+1)); echo "FAIL  build $flags"; cat "$work/err"; continue; fi
  if timeout 300 $PY -W ignore mail/server.py "$work/main" > "$work/res" 2>"$work/err"; then pass=$((pass+1)); echo "ok    $flags ($(tail -1 "$work/res"))"
  else fail=$((fail+1)); echo "FAIL  $flags"; tail -20 "$work/res"; grep -v 'auth_require_tls\|login_data' "$work/err" | tail -5; fi
done
rm -rf "$work"
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
