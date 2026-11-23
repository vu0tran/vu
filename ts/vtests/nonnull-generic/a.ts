export function f<T extends { a?: string | null; b: number }, K extends keyof T>(o: T, k: K) {
  const x = o[k]!;
  const y = o.b!;
  const z: number = x;
  return [x, y, z];
}
type C<T> = T extends string ? T | null : number;
export function g<T>(v: C<T>) { const w: string = v!; return w; }
