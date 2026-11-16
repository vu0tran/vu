// An accessor's read type is its getter's: a type parameter only a setter reads is independent.
interface Ref<T = any, S = T> { get value(): T; set value(_: S); }
declare const a: Ref<null, null | undefined>;
export const b: Ref<string | null> = a;
interface Obj<T, S> { get value(): T; set value(_: S); }
declare const c: Obj<null, null | undefined>;
export const d: Obj<string | null, string | null> = c;
declare const e: { get value(): null; set value(_: null | undefined) };
export const f: { get value(): string | null; set value(_: string | null) } = e;
declare const g: Ref<number>;
export const h: Ref<string> = g;
interface Unused<T> { x: number }
declare const u1: Unused<string>;
export const u2: Unused<number> = u1;
interface SetOnly<T> { set v(x: T); }
declare const s1: SetOnly<string>;
export const s2: SetOnly<number> = s1;
