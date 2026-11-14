declare class F { constructor(o: { a: number }, p?: string); }
declare const o: { m(a: string): number };
function t1(x: []) { return new F(...x); }
function t2(x: []) { return o.m(...x); }
function t3(x: [string, string]) { return o.m(...x); }
function t4(x: [{ a: string }]) { return new F(...x); }
function t5(x: [{ a: number }, string?]) { const r: string = o.m(...["a"] as [string]); return new F(...x); }
export {};
