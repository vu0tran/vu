declare const secured: { base: new () => { kind: string } };
class Derived extends secured.base {}
const n: number = new Derived().kind;
declare class Ag<R = string> { r: R; constructor(o?: number); }
declare const lib: { agent: typeof Ag & ((o?: number) => Ag) };
class T2<Q extends string = string> extends lib.agent<Q> { host(): this { return this; } }
const m: number = new T2<"x">().r;
declare const bad: { base: number };
class D3 extends bad.base {}
export {};
