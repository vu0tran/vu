import type { Foo as FooP, Baz } from './missing';
import * as ns from './c';
export function f(p: FooP): number { return p ? 1 : 2; }
export function h(): FooP { return 1 as any; }
export function k({ x }: { x: FooP }): number { return x ? 1 : 2; }
type R = Parameters<typeof f>[0];
type U = FooP | string;
type C<T> = T extends string ? T : number;
type G<T> = T[];
export type T1 = Parameters<typeof f>[0] | undefined;
export type T2 = ReturnType<typeof h> | null;
export type T3 = R | undefined;
export type T4 = Parameters<typeof k>[0]['x'] | undefined;
export type T5 = Parameters<typeof ns.g>[0] | undefined;
export type T6 = U | undefined;
export type T7 = C<FooP> | undefined;
export type T8 = NonNullable<FooP> | undefined;
export type T9 = Partial<FooP> | undefined;
export type T10 = Baz<string> | undefined;
export type T11 = G<FooP>[number] | undefined;
export type T12 = typeof ns.v | undefined;
export type T13 = ns.Q | undefined;
export type T14 = Awaited<ReturnType<typeof h>> | undefined;
