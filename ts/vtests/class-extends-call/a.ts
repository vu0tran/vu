export interface Shape { [k: string]: unknown }
export interface DtoClass<T> {
  new (data: T): T;
  schema: string;
  parse(data: unknown): T;
  extend<U extends Shape>(shape: U): DtoClass<T & U>;
}
declare function mk<T extends Shape>(shape: T): DtoClass<T>;
export const Z = { class: mk };

export class A extends Z.class({ a: 1, b: "x" }) {}
export class B extends A.extend({ c: true }) {}
export class C extends mk({ d: 2 }) {
  more = 3;
  get both(): number { return this.d + this.more; }
}
const a = new A({ a: 1, b: "y" });
const n: string = a.a;
const b = B.parse(null);
const s: number = b.c;
const p: number = A.schema;
const c = new C({ d: 3 });
const q: string = c.both;
const w: string = C.parse(1).d;
export class D extends Z.class(5) {}
class F extends Z.class({ f: 1 }) {
  constructor() { super({ f: 2 }); super.toString(); }
}
const g: string = new F().f;
const bi = new B({ a: 1, b: "s", c: true });
const bi1: string = bi.c;
const bi2: boolean = bi.a;
