// object relates as the global Object interface (its apparent type)
export {};
declare const o: object;
const a: Object = o;
declare function f(x: Object): void;
f(o);
const b: { toString(): string } = o;
const c2: { a?: number } = o;
const d: { a: number } = o;
const e: () => void = o;
