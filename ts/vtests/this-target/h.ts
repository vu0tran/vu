export {};
class A { a = 1; m(): this { return this; } }
class B extends A { b = 2; }
const x: A = new B();
const y: B = new A();
interface I { k: number; self(): this; f(x: this): void }
const i1: I = { k: 1, self() { return this; }, f(x) {} };
declare const ii: I;
const i2: I = { k: 1, self: () => ii, f: (x: I) => {} };
const i3: I = { k: 1, self: () => ii, f: (x: { k: number; z: 1 }) => {} };
interface J { k: number; z?: 1; self(): this }
const j1: J = { k: 1, z: 1, self: () => ({ k: 2, self: () => j1 }) };
class C { c = 1; clone(): this { return this; } }
const cc: C = { c: 2, clone() { return new C(); } };
