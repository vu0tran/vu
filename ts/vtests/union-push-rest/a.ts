// a union of arrays' push: one signature, its rest elements intersected
type H = { a: Array<(x: number) => void>; b: Array<(s: string) => void> };
export class C {
  h: H = { a: [], b: [] };
  add<K extends keyof H>(k: K, f: H[K][number], u: H['a'] | H['b'], ...fs: Array<H[K][number]>) {
    this.h[k].push(...fs);
    this.h[k].push(f);
    u.push(f);
    const pu: null = u.push;
    const n: string = u.push(() => {});
  }
}
export function g(x: number[] | string[], y: (number | string)[]) {
  x.push(1);
  x.push(...y);
  const r: null = x.unshift();
}
