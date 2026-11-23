// strict false: null and undefined out of unions and assignable to anything, implicit anys
// without errors, function parameters bivariant, call/apply/bind of Function, catch variables any
export {};
type Opts = { a?: number; b: string | undefined; c: boolean | null };
declare const o: Opts;
const x1: string = o.a;
const x2: number = o.b;
const x3: string = o.c;
function f(p, q?: number) { return p + q; }
const r: string = f(1);
let u = undefined;
u = 1;
let n = null;
const s: number = o.b.length;
function g({ k = 1 }: { k?: number }) { return k; }
const t: string = g({});
declare function cb(f: (x: string | number) => void): void;
cb((x: string) => {});
const fc = (a: number) => a;
const z: string = fc.call(null, 1);
try { } catch (e) { const ee: string = e.foo; }
