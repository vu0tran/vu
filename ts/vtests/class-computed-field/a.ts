// class fields with computed names the binder resolves: a literal constant, a namespace's
// literal constant, a unique symbol
const K = 'k';
declare namespace Rpc { const BRAND: 'brand'; }
const U: unique symbol = Symbol();
declare class D { [Rpc.BRAND]: never; [K]: number; }
class E { [K] = 1; [U]: string = 'u'; [Rpc.BRAND]?: boolean; }
declare const d: D;
const a: string = d.k;
const b: number = d.brand;
const e = new E();
const c: string = e.k;
const f: number = e[U];
const g: number = e.brand;
class F { [K]: number; }
