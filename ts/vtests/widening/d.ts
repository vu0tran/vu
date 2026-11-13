export {};
declare const k: boolean;
const w1 = [{ a: 1, c: 1 }, { a: 1, b: 2 }];
const y1: boolean = w1;
const w2 = [{ z: 1 }, { a: 1, b: 2 }, { c: "s" }];
const y2: boolean = w2;
let v2 = k ? { z: 1 } : k ? { a: 1, b: 2 } : { c: "s" };
const y3: boolean = v2;
const o = { p: k ? { a: 1 } : { b: 1 } };
const y4: boolean = o;
function f() { return k ? { a: 1 } : { b: "x" }; }
const y5: boolean = f();
const y6: boolean = [k ? { a: 1 } : { b: "x" }];
