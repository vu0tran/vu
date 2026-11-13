namespace N { export interface I { a: 1 } export const v = 1; export namespace M { export type T = string } }
import I = N.I;
import v = N.v;
import T = N.M.T;
export import W = N.v;
export const a: 'z' = null as unknown as I;
export const b: 'z' = v;
export const c: 'z' = null as unknown as T;
export const d: 'z' = W;
