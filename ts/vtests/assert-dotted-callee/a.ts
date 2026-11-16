// An expression statement's call is an assertion only when its callee is a dotted name: the
// callee of expect(...).toBe(...) isn't checked again outside the && narrowing.
interface L { version: number | number[]; name: string }
declare const result: L | null;
declare function expect<T>(a: T): { toBe(v: T): void };
expect(Array.isArray(result?.version) && result.version.includes(3.4)).toBe(true);
declare function ex2(a: boolean): { toBe(v: boolean): void };
ex2(Array.isArray(result?.version) && result.version.includes(3.4)).toBe(false);
declare function assertStr(x: unknown): asserts x is string;
declare const u: unknown;
assertStr(u);
export const len: number = u.length;
