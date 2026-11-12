// An intersection related to an object type through its members together: properties,
// call and construct signatures, index signatures (vitest's Mock as a function)
export {};
interface Mock { mock: { calls: any[] }; mockReturnValue(v: any): this }
type M = Mock & { (...args: any[]): any; new (...args: any[]): any } & {};
declare const m: M;
const f1: (a: string) => void = m;
const f2: (a: string) => number = m;
const o1: { mock: { calls: any[] } } = m;
const o2: { mock: { calls: string } } = m;
type A = { a: number } & { b: string };
declare const ab: A;
const x1: { a: number; b: string } = ab;
const x2: { a: number; b: number } = ab;
type I = { [k: string]: number } & { a: 1 };
declare const ii: I;
const y1: { [k: string]: number } = ii;
const y2: { [k: string]: string } = ii;
