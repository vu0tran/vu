// An argument that's a generic call inside a generic call: the inner function's contextual
// return type is the outer type parameter's constraint (inferTypeArguments' returnContext).
declare function mk2<U>(f: (n: number) => U): U[];
declare function f1<T extends any[] | [any]>(cases: ReadonlyArray<T>): { one: T };
const r3: null = f1(mk2((n) => ['a', n] as const));
declare function f2<T>(cases: ReadonlyArray<T>): { one: T };
const r4: null = f2(mk2((n) => ['a', n] as const));
declare function f3<T extends any[]>(cases: ReadonlyArray<T>): { one: T };
const r5: null = f3(mk2((n) => ['a', n] as const));
declare function id<U>(f: (n: number) => U): U;
const r7: null = f3([id((n) => ['a', n] as const)]);
declare function mk4<U>(f: (n: number) => U): U[];
declare function g2<T>(cases: ReadonlyArray<T>): { one: T };
declare function g3<T extends string>(cases: ReadonlyArray<T>): { one: T };
declare function g5<T extends { a: string }>(cases: ReadonlyArray<T>): { one: T };
declare function g6<T extends 'x' | 'y'>(cases: ReadonlyArray<T>): { one: T };
declare function id4<U>(f: (n: number) => U): U;
declare function h3<T extends string>(c: T): { one: T };
const a1: null = g2(mk4((n) => 'x'));
const a2: null = g3(mk4((n) => 'x'));
const a3: null = g5(mk4((n) => ({ a: 'x' })));
const a4: null = g6(mk4((n) => 'x'));
const a5: null = h3(id4((n) => 'x'));
const a6: null = g3(mk4((n) => { return 'x'; }));
declare function mk3<U>(): U[];
const r8: null = g2(mk3());
const r10: null = g2(mk4((n) => n));
declare function g4<T extends { a: 1 | 2 }>(cases: ReadonlyArray<T>): { one: T };
const r13: null = g4(mk4((n) => ({ a: 1 })));
// vitest's it.each: a readonly tuple from `as const` is mutable for the first overload
interface E {
	<T extends any[] | [any]>(cases: ReadonlyArray<T>): (fn: (...args: T) => void) => void;
	<T extends ReadonlyArray<any>>(cases: ReadonlyArray<T>): (fn: (...args: T[]) => void) => void;
}
declare const each: E;
interface Cron { name: string; timeoutMs: number | null }
declare const crons: Cron[];
each(crons.map((c) => [c.name, c] as const))((_name, cron) => {
  const t: null = cron;
  const s: null = _name;
});
