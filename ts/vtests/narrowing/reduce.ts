export function r4(f: [string, number][]) {
  return f.reduce((acc, cur) => acc + cur[1], 0);
}
export function r6(f: [string, number][]) {
  return f.reduce((acc, [, n]) => acc + n, 0);
}
declare function red<U>(cb: (p: U, c: [string, number]) => U, init: U): U;
export const r7 = red((acc, [_, n]) => acc + n, 0);
declare function red2<U>(cb: (p: U, c: [string, number]) => U, init: U): U;
export const r8 = red2((acc, c) => acc + c[1], 0);
