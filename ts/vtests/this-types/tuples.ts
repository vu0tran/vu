// Readonly<tuple> is a readonly tuple; a rest parameter of a tuple type gives each parameter its
// element and prints expanded
declare const a: readonly ['fatal', true];
const b: Readonly<[any, any]> = a;
const c: readonly [any, any] = a;
type K = (readonly ['fatal', true]) extends Readonly<[any, any]> ? 1 : 0;
const k: K = 5;
type K2 = (readonly ['fatal', true]) extends readonly [any, any] ? 1 : 0;
const k2: K2 = 5;
type K3 = ['fatal', true] extends Readonly<[any, any]> ? 1 : 0;
const k3: K3 = 5;
declare const q: (fn: (...args: ['a' | 'b', 1]) => void) => void;
q((x, y) => { const n: { a: 1 } = x; const m: { a: 1 } = y; });
declare const hh: (fn: (x: 'a' | 'b', y: 1) => void) => void;
hh((x, y) => { const n: { a: 1 } = x; const m: { a: 1 } = y; });
declare const q2: (fn: (...args: readonly ['a' | 'b', 1]) => void) => void;
q2((x, y) => { const n: { a: 1 } = x; const m: { a: 1 } = y; });
declare const w: (...args: ['a' | 'b', 1]) => void;
const y: number = w;
declare const w2: (x: string, ...rest: [number, boolean?]) => void;
const y2: number = w2;
declare const w3: (...args: [a: string, b?: number]) => void;
const y3: number = w3;
declare const w4: (...args: [string, ...number[]]) => void;
const y4: number = w4;
type T5 = [string, number];
declare const w5: (...args: T5) => void;
const y5: number = w5;
