type R = { kind: 'a'; options: readonly [string, ...string[]] } | { kind: 'b' };
export function f(s: Set<string>): R {
  const it = s.values();
  const first = it.next();
  if (first.done) return { kind: 'b' };
  return { kind: 'a', options: [first.value, ...it] };
}
export function g(m: Map<string, number>): [number, ...number[]] {
  return [1, ...m.values()];
}
const t: [string, ...number[]] = ['a', ...new Set([1, 2])];
const n: string = t;
const t2: [string, ...number[]] = ['a', ...new Set(['x'])];
