export class C<T = unknown, D = any> { t?: T; d?: D; }
export type IA<T = unknown, D = any> = C<T, D>;
type I0<T = unknown, D = any> = C<T, D>;
export type IB<T = unknown, D = any> = I0<T, D>;
export namespace ns { export type IN<T = unknown, D = any> = I0<T, D>; }
declare const e: unknown;
const l1: number = e as IA;
const l2: number = e as IB;
const l3: number = e as I0<number>;
