// a call no overload matches, none generic: its signature the candidates' union (createUnionOfSignaturesForOverloadFailure), returning the intersection of their returns
declare const tuples: [number, string][];
declare function f(a: string): { s: 1 };
declare function f(a: number, b?: boolean): { n: 2 };
declare function g(...xs: string[]): string;
declare function g(a: number, ...xs: boolean[]): number;
export const a: number = [].concat(tuples, [[1, 'x']]);
export const b: number = f(true);
export const c: number = g({});
export const d: string = f(null as unknown as object).s;
