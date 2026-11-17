export {};
class A { static s = 1; static m(): number { return 1; } i = "x"; im(): string { return ""; } }
class B extends A {
  static m(): number { const q: string = super.m(); const r: string = super.s; return 2; }
  static z = super.s;
  im(): string { const v: number = super.im(); return ""; }
  static f = () => { const u: string = super.m(); };
}
const bz: string = B.z;
declare function mk(): { new (): { a: number }; st: string; sm(): number };
class C extends mk() {
  static g() { const x: number = super.st; return super.sm(); }
}
const cg: string = C.g();
