async function* g0() {}
export const a: 'z' = g0();
async function* g1() { yield 1; yield Promise.resolve('s'); return true; }
export const b: 'z' = g1();
export const p = Object.getPrototypeOf(g0);
export const f = async function* () { yield 2; };
export const c: 'z' = f();
export async function use() { for await (const x of g1()) { const q: 'z' = x; } }
export async function use2(xs: Promise<number>[], s: AsyncIterable<string>) {
  for await (const x of xs) { const q: 'z' = x; }
  for await (const y of s) { const q: 'z' = y; }
}
