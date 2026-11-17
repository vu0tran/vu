export {};
type noUndefined<T> = T extends undefined ? never : T;
type Writeable<T> = { -readonly [P in keyof T]: T[P] };
function f1<const T extends [string, ...string[]]>(v: T[number]) {
  const a: noUndefined<Writeable<T>[number] | undefined> = v;
  const b: noUndefined<T[number]> = v;
  const c: noUndefined<T[number] | undefined> = v;
  const d: noUndefined<Writeable<T>[number]> = v;
}
function f2<U extends string>(v: U) {
  const a: noUndefined<U> = v;
  const b: noUndefined<U | undefined> = v;
  const c: noUndefined<string> = v;
}
function f3<U>(v: U) {
  const a: noUndefined<U> = v;
}
type NN<T> = T extends null ? never : T;
function f4<U extends number>(v: U) {
  const a: NN<U> = v;
  const b: Exclude<U, undefined> = v;
}
