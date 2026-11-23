// as const array literals whose contextual type is a type parameter constrained to mutable arrays
// (vitest's each, T extends any[] | [any]): mutable tuples, checkArrayLiteral's isMutableArrayLikeType
export {};
declare function f<T extends any[] | [any]>(cases: ReadonlyArray<T>): T;
const w = f([[true, null, 'A'], [false, 'r', 'B']] as const);
interface E { <T extends any[] | [any]>(cases: ReadonlyArray<T>): [1, T]; <T extends ReadonlyArray<any>>(cases: ReadonlyArray<T>): [2, T] }
declare const e: E;
const v = e([[true, null, 'A'], [false, 'r', 'B']] as const);
const vn: number = v;
