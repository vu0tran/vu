export {};
type Ex<T, U> = T extends U ? never : T;
type Ext<T, U> = T extends U ? T : never;
function f1<U extends string>(v: U) {
  const a: Ex<U, number> = v;
  const b: Ext<U, string> = v;
  const c: Ext<U, number> = v;
  const d: NonNullable<U> = v;
  const e: Ex<U, "x"> = v;
  const g: Exclude<U, null> = v;
}
function f2<K extends "a" | "b">(k: K, o: { [P in K]: number }) {
  const a: Ex<K, "c"> = k;
  const b: Ex<K, "a"> = k;
  const c: Ext<K, string> = k;
}
function f3<T extends object>(t: T) {
  const r: Readonly<T> = t;
  const p: Partial<T> = t;
  const q: Required<T> = t;
  const w: { -readonly [P in keyof T]: T[P] } = t;
  const x: { [P in keyof T]: T[P] | 1 } = t;
}
function f4<T extends number>(t: T, u: T & {}, z: T & bigint) {
  const a: T = u;
  const b: never = z;
  const c: string = u;
}
function f5<T>(t: T) { const a: NonNullable<T> = t; const b: Ext<T, unknown> = t; }
