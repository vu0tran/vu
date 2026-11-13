// for-in keys of generic types: Extract<keyof T, string>; object comparable with object types
export {};
function q1<T>(s: T) {
	for (const i in s) { const e: number = i; }
}
function q2<T>(s: T) {
	if (typeof s !== 'object' || s === null) return;
	for (const i in s) { const e: number = i; }
}
function f3<T>(s: T) {
	if (typeof s !== 'object' || s === null) return;
	s;
	for (const i in s) { const e: number = i; }
}
function f4<T>(s: T) {
	if (typeof s !== 'object') return;
	for (const i in s) { const e: number = i; }
}
function f5<T extends object>(s: T) {
	for (const i in s) { const e: number = i; }
}
function f6(s: { a: 1 }) {
	for (const i in s) { const e: number = i; }
}
function findKey<Value, Obj extends { [key in string | number]: Value }>(
  object: Obj,
  predicate: (value: Value) => boolean,
): keyof Obj | undefined {
  for (const key in object) {
    const n: number = object[key];
    if (predicate(object[key])) return key;
  }
  return undefined;
}
function r1<Value, Obj extends { [key in string | number]: Value }>(object: Obj, k: Extract<keyof Obj, string>) {
  const n: number = object[k];
}
function r2<Value, Obj extends { [key: string]: Value }>(object: Obj, k: Extract<keyof Obj, string>) {
  const n: number = object[k];
}
function h1<T extends object | string>() { const c1: any[] = []; return c1 as T; }
function h2<T extends { a: 1 } | string>() { const c1: { a: 1, b: 2 } = null!; return c1 as T; }
function h3<T extends { a: 1, b: 2 } | string>() { const c1: { a: 1 } = null!; return c1 as T; }
function h4<T extends { a: 1, b: 2 }>() { const c1: { a: 1 } = null!; return c1 as T; }
function h5<T extends { a: 1 }>() { const c1: { a: 1, b: 2 } = null!; return c1 as T; }
function h6<T extends Date | string>() { const c1: object = null!; return c1 as T; }
function h7<T extends object | string>() { const c1: number[] = []; return c1 as T; }
function h8<T extends { x?: number } | string>() { const c1: number[] = []; return c1 as T; }
function h9<T extends { x?: number } & object | string>() { const c1: number[] = []; return c1 as T; }
