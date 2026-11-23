// T & {} keeps the {} written (a type literal, with an implicit index signature): NonNullable<unknown> is assignable to Record<string, number>, as a default too.
type NN<T> = T & {};
declare const e3: NN<unknown>;
declare const e4: unknown & {};
const r3: Record<string, number> = e3;
const r4: Record<string, number> = e4;
declare const f1: NonNullable<unknown>;
declare const f2: {};
const s1: Record<string, number> = f1;
const s2: Record<string, number> = f2;
declare function q3<A, T extends Record<string, number> = NonNullable<unknown>>(a: A): [A, T];
const x3 = q3(1);
const y3: number = x3;
declare function q5<A, T extends Record<string, number> = {}>(a: A): [A, T];
const y5: number = q5(1);
