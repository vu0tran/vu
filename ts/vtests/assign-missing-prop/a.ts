declare const o: { a: { b: { c: string } } };
// @ts-expect-error nope
o.a.b.ccc = { d: "4" };
// @ts-expect-error nope
o.a.b.ccc.d = "x";
// @ts-expect-error nope
const v = o.a.b.ccc;
declare let p: { q: string };
// @ts-expect-error nope
p.zz = 1;
// @ts-expect-error nope
p.zz;
export {};
