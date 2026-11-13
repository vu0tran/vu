export class A {
  a: number; b: number; c: number; d: number;
  constructor(x: boolean, y: boolean) {
    if (x) { this.a = 1; this.b = 1; } else { this.a = 2; }
    if (y) throw new Error();
    this.c = this.d = 3;
  }
}
export class B {
  a: number; b: number;
  constructor(x: boolean) {
    if (x) { this.a = 1; return; }
    this.a = 2;
    { this.b = 1; }
  }
}
export class C2 {
  a: number;
  constructor(x: boolean) { if (x) this.a = 1; }
}
