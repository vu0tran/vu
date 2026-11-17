export interface Shape { [k: string]: unknown }
export interface DtoClass<T> {
  new (data: T): T;
  parse(data: unknown): T;
  extend<U extends Shape>(shape: U): DtoClass<T & U>;
}
declare function mk<T extends Shape>(shape: T, opts?: { strict?: boolean }): DtoClass<T>;
declare function mk2(): { new (): { x: number }; new (a: string): { x: number } };
declare function mk3(): { new (): { x: number }; new (a: string): { y: number } };
declare function mk4(): { new <Q>(q: Q): { q: Q } };
const used = new Late({ z: 1 });
export class Late extends mk({ z: 1 }) {}
export class Bad extends mk({ a: 1 }, { strict: "yes" }) {}
export class Bad2 extends mk({ a: 1 }, { strictt: true }) {}
export class Over extends mk({ a: 1 }) {
  a: string = "x";
}
export class M2 extends mk2() {}
const m2 = new M2("s");
const m2b: string = new M2().x;
export class M3 extends mk3() {}
export class M4 extends mk4()<string> {}
const m4: number = new M4("x").q;
const K = class extends mk({ k: 1 }) {};
const kk: string = new K({ k: 2 }).k;
export class NoNew extends mk({ a: 1 }).parse {}
export class Undef extends notThere({}) {}
let v: string = used.z;
