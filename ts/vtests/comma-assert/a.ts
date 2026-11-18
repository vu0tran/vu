declare function ok(v: unknown, m?: string): asserts v;
declare const x: string | undefined;
export function f() {
  (0, ok)(x);
  const y: string = x;
}
declare const o: { f(): number };
let z = 0;
export const r1 = (0, o.f)();
export const r2 = (1, o.f)();
export const r3 = (z = 1, z + 1);
export const r4 = ('a', !z, z++, 3);
export const r5 = (z ? 1 : 2, typeof z, 4);
