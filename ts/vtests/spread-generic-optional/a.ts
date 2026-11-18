interface Cfg { a?: number; b: string; readonly c: boolean }
export class K<T extends Cfg> {
  constructor(public d?: T) {}
  m(x?: T): Cfg {
    const r = { ...this.d, ...x };
    return r;
  }
  n<U>(u: U | undefined) { const z = { ...u, k: 1 }; const w: number = z; }
}
declare const y: Cfg;
const r2 = { ...y, k: 1 };
export const q2: number = r2;
declare const x: Cfg | undefined;
export const q3: number = { ...x };
