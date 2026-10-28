// fannkuch-redux: a straight port of bench/fk.c
const n = process.argv[2] ? parseInt(process.argv[2], 10) : 7;
const perm = new Int32Array(16), perm1 = new Int32Array(16), count = new Int32Array(16);
let maxFlips = 0, checksum = 0, permCount = 0, r = n;
for (let i = 0; i < n; i++) perm1[i] = i;
outer: for (;;) {
  while (r !== 1) { count[r - 1] = r; r--; }
  for (let i = 0; i < n; i++) perm[i] = perm1[i];
  let flips = 0, k;
  while ((k = perm[0]) !== 0) {
    for (let lo = 0, hi = k; lo < hi; lo++, hi--) { const t = perm[lo]; perm[lo] = perm[hi]; perm[hi] = t; }
    flips++;
  }
  if (flips > maxFlips) maxFlips = flips;
  checksum += permCount % 2 === 0 ? flips : -flips;
  for (;;) {
    if (r === n) { console.log(`${checksum}\nPfannkuchen(${n}) = ${maxFlips}`); break outer; }
    const first = perm1[0];
    for (let i = 0; i < r; i++) perm1[i] = perm1[i + 1];
    perm1[r] = first;
    if (--count[r] > 0) break;
    r++;
  }
  permCount++;
}
