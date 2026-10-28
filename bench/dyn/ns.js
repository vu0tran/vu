// nsieve: a straight port of bench/ns.c
function nsieve(m) {
  const flags = new Uint8Array(m).fill(1);
  let count = 0;
  for (let i = 2; i < m; ++i)
    if (flags[i]) { ++count; for (let j = i << 1; j < m; j += i) flags[j] = 0; }
  console.log(`Primes up to ${String(m).padStart(8)} ${String(count).padStart(8)}`);
}
const m = parseInt(process.argv[2], 10);
for (let i = 0; i < 3; i++) nsieve(10000 << (m - i));
