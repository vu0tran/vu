declare class F { constructor(o?: { a: number }); }
declare function f(a: string, b?: number): void;
declare function g(a: string, b: number): void;
function t1(...args: ConstructorParameters<typeof F>) { return new F(...args); }
function t2(...args: [string, number?]) { f(...args); }
function t3(...args: [string, string?]) { f(...args); }
function t4(...args: [number]) { f(...args); }
function t5(x: [number?]) { f("a", ...x); }
function t6(x: [string?]) { f("a", ...x); }
function t7(x: [string, number?]) { g(...x); }
function t8(x: [string, number]) { g(...x); }
function t9(x: readonly [string, number]) { g(...x); }
function t10(x: [string, number, number]) { g(...x); }
function t11(x: []) { f(...x); }
export {};
