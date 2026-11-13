export function mk(n: number) {
  return class Inner {
    a: string;
    b = n;
    static count = 0;
    constructor() { this.a = 'x'; Inner.count++; }
    m(): number { return this.a; }
    f = () => this.b;
  };
}
export const K = mk(1);
export const k: 'z' = new K().f();
export const G = class<T> { constructor(public v: T) {} get(): T { return this.v; } };
export const g: 'z' = new G(1).get();
export const xs = [1, 2].map(() => class { q?: number; });
for (const x of [1]) { const Q = class { r = x; }; const qq: 'z' = new Q().r; }
export const bad = class { p: number; };
