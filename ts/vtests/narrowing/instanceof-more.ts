// instanceof: a class extending an imported class or Error derives from it; any narrows to the
// class; neither related, their intersection; larger unions; new.target in a constructor
export {};
class Base { b = 1; }
class Derived extends Base { d = 2; }
class Err2 extends Error { e = 1; }
declare const x: Error | undefined;
if (x instanceof Err2) { const n: number = x; }
declare const y: any;
if (y instanceof Date) { const n: number = y; } else { const m: number = y; }
declare const j: { [k: string]: string };
if (j instanceof Error) { const n: number = j; }
declare const big: string | number | boolean | Date | string[] | number[] | { a: 1 } | { b: 2 } | { c: 3 } | { d: 4 } | null;
if (big instanceof Date) { const n: number = big; } else { const m: number = big; }
class E { constructor() { if (new.target === E) { const n: number = new.target; } } }
class F extends E { constructor() { super(); const g = () => new.target; const n: number = g(); } }

