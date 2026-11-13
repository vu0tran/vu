export {};
interface PP<T = unknown> { value: T; issues: string[] }
interface CI<T> { def: { c: string }; check(payload: PP<T>): void; onattach: ((s: unknown) => void)[] }
interface Ck<in T = never> { _zod: CI<T> }
declare const a: Ck<string>[] | undefined;
const b: Ck<never>[] | undefined = a;
declare const c: Ck<string>;
const d: Ck<never> = c;
interface Box<out T> { v: T }
declare const e: Box<"a">;
const f: Box<string> = e;
declare const g: Ck<never>;
const h: Ck<string> = g;
interface Inv<in out T> { v: T }
declare const i1: Inv<"a">;
const i2: Inv<string> = i1;
