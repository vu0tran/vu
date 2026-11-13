export {};
declare const k: boolean;
let v = k ? { a: 1 } : { a: 1, b: 2 };
const n1: string = v.a;
const n2: number | undefined = v.b;
const n3: string = v.b;
const w = [{ a: 1 }, { a: "s", b: 2 }];
const n4: number = w[0].b;
function f() { return k ? { a: 1 } : { c: "x" }; }
const r = f();
const n5: number = r.c;
