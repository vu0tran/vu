// A parameter with a type and an initializer: the initializer is checked against the type.
export function f(a: string = 5): string { return a; }
export const g = (b: number = "x") => b;
class C {
  m(z: number = "q") { return z; }
  constructor(private readonly now: () => number = Date.now, n: 1 | 2 = 2) { void this.now; void n; }
}
export const c = new C();
export function h(o: { x?: number } = { x: 1, y: 2 }, k: "a" | "b" = "a"): number { return (o.x ?? 0) + k.length; }
export function u(t: string | undefined = undefined, v: number = undefined): string { return (t ?? "") + v; }
export function wd<T extends object>(d: T, o: Partial<T> = {}, r: { readonly [K in keyof T]?: T[K] } = {}): T { void r; return { ...d, ...o }; }
