// calling a union of functions with different parameters: the combined signature
export {};
declare const v: string | number;
const a = v.toString(); const a1: boolean = a;
v.toString(16);
declare const f: ((x: string) => number) | ((y: number, z?: boolean) => string);
const b = f(1 as never); const b1: boolean = b;
f("s");
const g1: number = f;
declare const h: ((x: { a: 1 }) => void) | ((x: { b: 2 }) => void);
h({ a: 1, b: 2 });
h({ a: 1 });
declare const w: string | number | boolean | undefined;
const s = w?.toString().toLowerCase(); const s1: number = s;
