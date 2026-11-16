declare const s: string;
declare const u: string | undefined;
export class A {
  a: string;
  b: string;
  c: string;
  d: string;
  constructor() {
    this.a ??= s;
    this.b ||= s;
    this.c &&= s;
    this.d ??= u;
  }
}
