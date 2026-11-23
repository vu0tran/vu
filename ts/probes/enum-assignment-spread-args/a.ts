// A spread argument of a union of tuples, a generic array or a homomorphic mapped type over one:
// its elements (the base constraint's, the apparent type's).
enum E { A = 0, B = 1 }
declare function f(...a: E[]): void;
declare function g(a: E, b: E): void;
declare const nums: number[];
declare const tup: [number, number];
f(...nums);
g(...tup);
export function h<T extends number[]>(xs: T, fn: (...a: E[]) => void) {
  fn(...xs);
}
export function k<T extends readonly unknown[]>(xs: { [K in keyof T]: NonNullable<T[K]> }, fn: (...a: { [K in keyof T]: NonNullable<T[K]> }) => void) {
  fn(...xs);
}
export function p<T extends (...a: any[]) => any>(fn: T) {
  return (...args: Parameters<T>) => fn(...args);
}
declare const s: Set<number>;
f(...s);
declare const ut: [number] | [number, number];
f(...ut);
declare const ue: [E] | [E, E];
f(...ue);
export function q<T extends E[]>(xs: T) {
  f(...xs);
}
