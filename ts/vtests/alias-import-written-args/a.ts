// An alias named through an import: its alias arguments are the written ones, the defaults left
// out (getTypeFromTypeAliasReference); an object type too. A local alias keeps them all.
import type { Ob, In } from './b';

declare const ob: Ob;
declare const ob2: Ob<'x'>;
declare const in1: In<string>;
declare const in2: In<string, number>;
export const x1: number = ob;
export const x2: number = ob2;
export const x3: number = in1;
export const x4: number = in2;
declare function f<T extends Ob>(x: In<T>): T;
export const x5: number = f;
export const x6: number = f(null!);
type L<A extends string = string> = { l: A };
declare const l: L;
export const x7: number = l;
