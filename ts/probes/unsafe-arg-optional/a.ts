// a parameter written with ? has undefined in its type (getTypeOfSymbol); one with an initializer does not
import { E } from '@gql';
declare const x: any;
declare const e: E;
export function f(a?: number | null, b: number | null = 1, c?: string, d: string = '', ...r: number[]) { return [a, b, c, d, r]; }
f(x, x, x, x, x);
f(e, e, e, e, e);
export const g = (a?: { k: 1 }, b = 2) => [a, b];
g(x, x);
interface I { m(a?: number): void; n: (a?: string) => void }
declare const i: I;
i.m(x); i.n(x);
declare function h<T>(a?: T): T;
h<string>(x);
