// Spread arguments to new and super; an array spread no rest parameter takes is TS2556
declare const C: new (...a: unknown[]) => Record<PropertyKey, unknown>;
function f(...args: unknown[]) { const x = new C(...args); const n: number = x; }
class D { constructor(public a: number, ...r: string[]) {} }
declare const xs: string[];
const d = new D(1, ...xs);

declare const ns: number[];
const d3 = new D(1, ...ns);
class E extends D { constructor(...r: string[]) { super(1, ...r); } }
export {};
const d2 = new D(...xs);
declare function g(a: string, b: string): number;
const r1: string = g(...xs);
const r2 = g('a', ...xs);
