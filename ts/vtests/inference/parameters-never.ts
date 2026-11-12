// Parameters<F>: a lone rest parameter gives its own type, others a labeled tuple; a function
// expression whose end isn't reached returns never; this through an intersection is the whole
export {};
type Proc = (...args: any[]) => any;
type P1 = Parameters<Proc>;
const p1: number = null as any as P1;
type P2 = Parameters<() => Promise<void>>;
const p2: number = null as any as P2;
type P3 = Parameters<(a: string, b?: number) => void>;
const p3: number = null as any as P3;
type P4 = Parameters<(a: string, ...r: boolean[]) => void>;
const p4: number = null as any as P4;
const f1 = async () => { throw new Error('x'); };
const n1: number = f1;
const f2 = () => { throw new Error('x'); };
const n2: number = f2;
function f3() { throw new Error('x'); }
const n3: number = f3;
const o = { m() { throw 1; } };
const n4: number = o.m;
const f5 = function () { while (true) {} };
const n5: number = f5;
interface Inst { ret(v: number): this; calls: number }
type Mk = Inst & { (): void };
declare const mk: Mk;
const back: Mk = mk.ret(1);
const nope: number = mk.ret(1);
