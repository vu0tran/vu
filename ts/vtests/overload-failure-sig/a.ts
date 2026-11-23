// a call no overload fits: with a generic candidate, the longest one instantiated is its signature (getCandidateForOverloadFailure)
declare const rqIds: unknown[];
type Ev = { a: number };
export const m = new Map<string, Ev[]>(rqIds.map((id) => { return [id, []]; }));
const n1: number = m;
declare function f(a: string): string;
declare function f(a: number): number;
const r1: boolean = f(true);
declare function g<T>(a: T[], b: string): T;
declare function g<T>(a: T): T;
const r2: boolean = g([1], 2);
const r3: boolean = g([1], 2, 3);
export {};
