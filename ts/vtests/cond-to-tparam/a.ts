type Prim = string | number | boolean | null | undefined;
type DP<T> = T extends Prim ? T : T extends (...a: any[]) => unknown ? T | undefined : T extends object ? { [K in keyof T]?: DP<T[K]> } : unknown;
export function f<TData>(d: DP<TData>, x: TData): TData {
  const y: TData = d;
  return x;
}
type Id<T> = T extends string ? T : T;
export function g<T>(v: Id<T>): T {
  return v;
}
export function h<T, U>(d: DP<T>): U | DP<T> {
  return d;
}
