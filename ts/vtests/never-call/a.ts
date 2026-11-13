declare function fail(msg?: string): never;
const arrowFail = () => { throw new Error(); };
const typedFail: (m: string) => never = (m) => { throw new Error(m); };
namespace N { export function fail(): never { throw 1; } }
declare function gfail<T>(x: T): never;
declare function ov(x: string): never;
declare function ov(x: number): number;
declare var proc: { exit(code?: number): never };
declare const proc2: { exit(code?: number): never };
const proc3 = { exit(): never { throw 1; } };
function a1(x: string | undefined): string { if (!x) arrowFail(); return x; }
function a2(x: string | undefined): string { if (!x) typedFail("m"); return x; }
function a3(x: string | undefined): string { if (!x) N.fail(); return x; }
function a4(x: string | undefined): string { if (!x) gfail(1); return x; }
function a5(x: string | undefined): string { if (!x) ov("s"); return x; }
function a6(x: string | undefined): string { if (!x) ov(1); return x; }
function a7(x: string | undefined): string { if (!x) proc.exit(1); return x; }
function a8(x: string | undefined): string { if (!x) proc2.exit(1); return x; }
function a9(x: string | undefined): string { if (!x) proc3.exit(); return x; }
function b1(): number { arrowFail(); }
function b2(): number { typedFail("x"); }
function b3(): number { (fail)(); }
function b4(): never { fail(); }
function b5(): never { arrowFail(); }
const f1 = () => { fail(); };
const r1: string = f1();
const f2 = function () { fail(); };
const r2: string = f2();
function f3() { fail(); }
const r3: string = f3();
type U = { k: "a"; a: number } | { k: "b"; b: string };
function sw(u: U): number {
  switch (u.k) {
    case "a": return u.a;
    case "b": return 1;
    default: fail();
  }
}
function lp(xs: (string | undefined)[]): string {
  for (const x of xs) { if (x === undefined) fail(); return x; }
  return "";
}
function tr(): number {
  try { return 1; } catch (e) { fail(); }
}
function tr2(): number {
  try { fail(); } finally { }
}
class K {
  m(x: string | undefined): string { if (!x) this.fail(); return x; }
  n(): number { const g = () => { this.fail(); }; g(); }
  o(): number { [1].forEach(() => this.fail()); }
  static s(): number { K.sfail(); }
  static sfail(): never { throw 1; }
  private fail(): never { throw 1; }
}
function nested(x: string | undefined): string {
  if (!x) { console.log(1); fail(); }
  return x;
}
function both(x: number | string): number {
  if (typeof x === "number") { return x; } else { fail(); }
}
function opt(o?: { f(): never }): number { o?.f(); }
export {};
