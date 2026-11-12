// this in a function expression assigned to a property: the object's type
declare global { interface BigInt { toJSON?(): string } }
BigInt.prototype.toJSON = function () { const n: number = this; return this.toString(); };
const o = { a: 1, f: undefined as undefined | (() => number) };
o.f = function () { return this.a; };
export {};
