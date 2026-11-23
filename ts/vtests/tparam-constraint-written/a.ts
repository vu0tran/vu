declare class Box<T = { a: string }> { v: T }
declare namespace NS { class In<T = number> { w: T } }
interface Db<Q> {
  insert<TT extends Box>(t: TT): Q;
  ins2<TT extends NS.In>(t: TT): Q;
  ins3<TT extends Box<number>>(t: TT): Q;
  ins4<TT extends Array<Box>>(t: TT): Q;
}
declare const db: Db<string>;
const y1: null = db.insert;
const y2: null = db.ins2;
const y3: null = db.ins3;
const y4: null = db.ins4;
declare function g<T extends Box>(t: T): void;
const y5: null = g;
const y6: null = d2.m;
interface Db2<Q> { m<T extends Box<Q>>(t: T): void }
declare const d2: Db2<string>;
const y6: null = d2.m;
