// property and element reads of a type with a union constraint in a constraint position
interface H { a: ((x: number) => void)[]; b: ((s: string) => void)[] }
interface O { kind: 'x' | 'y'; v: string | number }
export class K {
  handlers: H = { a: [], b: [] };
  add<K2 extends keyof H>(name: K2, f: H[K2][number]) {
    const n: string = this.handlers[name].length;
    const l = this.handlers[name];
    const q: string = l.length;
  }
}
export function g<T extends O | { kind: 'z'; v: boolean }>(o: { t: T }) {
  const k: number = o.t.kind;
  const v: null = o.t.v;
  if (o.t.kind === 'x') { const w: null = o.t; }
}
export function h<T extends string | number>(o: { t: T }, arr: T[]) {
  const s: null = o.t.toString();
  const e: null = arr[0].valueOf();
}
