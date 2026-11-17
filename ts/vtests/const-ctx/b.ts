export {};
declare function f(x: number[]): void;
f([1, 2] as const);
declare function g<T>(x: T[]): T;
const g1: string = g([1, 2] as const);
declare function h(x: readonly number[] | string[]): void;
h(["a"] as const);
h([1] as const);
function r(): { k: string[] } { return { k: ["a"] } as const; }
const t1: [number, ...string[]] = [1, "a", "b"] as const;
const t2: readonly [number, string] = [1, "a"] as const;
const n2: number = t2;
const o: { a: readonly string[]; b: string[] } = { a: ["x"], b: ["y"] } as const;
const o2: { a?: Record<string, number[]> } = { a: { q: [1] } } as const;
declare const anyc: any;
const an: any = [1] as const;
const unk: unknown = [1] as const;
const n3: number = unk;
