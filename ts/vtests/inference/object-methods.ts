interface H<T> { get?(target: T, p: string): any }
declare function mk<T extends object>(t: T, h: H<T>): T;
export function w1<T extends object>(target: T): T {
  return mk(target, { get(o, k) { return k.length > 1 ? null : undefined; } });
}
export function w2<T extends object>(target: T): T {
  return mk(target, { get(o, k) { const v: unknown = 1; return v !== null && typeof v === 'object' ? w2(v) : v; } });
}
export const w3 = mk({ a: 1 }, { get(o, k) { const v: unknown = 1; return v !== null && typeof v === 'object' ? w2(v) : v; } });
