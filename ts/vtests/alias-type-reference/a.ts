interface I<T = any> { (x: T): string; p: T }
interface J { j: 1 }
type H2 = I<number>;
type H3 = J;
type H4 = Array<number>;
type H5 = Promise<string>;
declare const b: H2;
declare const c: H3;
declare const d: H4;
declare const e: H5;
export const n2: number = b;
export const n3: number = c;
export const n4: number = d;
export const n5: number = e;
type G<T> = Promise<T>;
declare const g: G<number>;
export const n6: number = g;
async function f(): G<number> { return 1; }
export const n7: number = f();
