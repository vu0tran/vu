#!/bin/sh
# Rebuilds the compiler, compiler/vuc, from its Vu source after a change to it:
#   1. without a compiler/vuc yet, bootstrap.sh builds one from vuc_seed.c;
#   2. tools/gen_runtime.vu turns the C runtime in rt/ into runtime_gen.vu, and the parts are joined
#      into vuc.vu (Vu has no modules for the compiler's own source yet);
#   3. the current vuc builds vuc.vu (stage 1), stage 1 builds it (stage 2), and stage 2 builds it once
#      more: that C must equal stage 2's (a fixed point). Stage 2 becomes compiler/vuc and its C the new
#      vuc_seed.c.
# A failure leaves the working compiler and the seed as they were.
cd "$(dirname "$0")" || exit 1
[ -x vuc ] || ./bootstrap.sh || exit 1
export VU_STD="$(cd .. && pwd)/std"
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
./vuc run ../tools/gen_runtime.vu || exit 1
cat c1_front.vu c2_types.vu c3_expr.vu c3b_calls.vu c4_stmt.vu c5_build.vu runtime_gen.vu > vuc.vu
./vuc build vuc.vu --debug -o "$work/s1" || { echo "FAIL: the current compiler can't build vuc.vu"; exit 1; }
"$work/s1" build vuc.vu -o "$work/s2" --emit-c "$work/2.c" || { echo "FAIL: stage 1 can't build vuc.vu"; exit 1; }
"$work/s2" build vuc.vu --debug -o "$work/s3" --emit-c "$work/3.c" || { echo "FAIL: stage 2 can't build vuc.vu"; exit 1; }
if ! cmp -s "$work/2.c" "$work/3.c"; then echo "FAIL: no fixed point (stage 2 and stage 3 make different C)"; exit 1; fi
cp "$work/s2" vuc.new && mv vuc.new vuc
cp "$work/2.c" vuc_seed.c
echo "ok   compiler rebuilt: fixed point, $(wc -l < vuc_seed.c) lines of C"
