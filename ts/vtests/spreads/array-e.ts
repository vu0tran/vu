// spreading arrays into object literals: Array's members, related to arrays
export {};
declare const arr: number[];
const r = { ...arr };
const b1: { [n: number]: number } = r;
const b2: { [Symbol.iterator](): ArrayIterator<number> } = r;
const b3: { sort(compareFn?: (a: number, b: number) => number): number[] } = r;
const b4: { readonly [Symbol.unscopables]: any } = r;
const b6: { map<U>(callbackfn: (value: number, index: number, array: number[]) => U, thisArg?: any): U[] } = r;
const b7: { length: number } = r;
const b8: { toString(): string } = r;
