declare const o: { a: { b: { c: string } } };
o.a.b.ccc = { d: "4" };
o.a.b.ccc.d = "x";
const v = o.a.b.ccc;
declare let p: { q: string };
p.zz = 1;
p.zz;
export {};
