// A type predicate whose type is generic, on a reference of a concrete type.
type EnumKey<E> = keyof E;
declare function isEnumKey<E extends Record<string, string>>(e: E, key: string): key is EnumKey<E> & string;
export function assertEnumKey<E extends Record<string, string>>(e: E, key: string): EnumKey<E> {
  if (isEnumKey(e, key)) {
    const n: number = key;
    return key;
  }
  const m: number = key;
  throw new Error("x");
}
function isValidKey<Map extends object>(key: PropertyKey, record: Map): key is keyof Map {
  return Object.hasOwn(record, key);
}
export function f<Map extends object>(map: Map) {
  return (value: PropertyKey) => {
    if (!isValidKey(value, map)) {
      const a: number = value;
      return null;
    }
    const b: number = value;
    return map[value];
  };
}
function isStr<T extends string>(x: string, t: T): x is T { return x === t; }
export function g<T extends string>(x: string, t: T) {
  if (isStr(x, t)) { const n: number = x; } else { const m: number = x; }
}
declare function isKey<E>(e: E, key: string): key is Extract<keyof E, string>;
export function h<E>(e: E, key: string) {
  if (isKey(e, key)) { const n: number = key; } else { const m: number = key; }
}
// @ts-ignore (2677)
declare function isK<E extends object>(e: E, key: string): key is keyof E & {};
export function k<E extends object>(e: E, key: string): keyof E {
  if (isK(e, key)) { const n: number = key; return key; }
  throw new Error("x");
}
// @ts-ignore (2677)
declare function isK2<E extends { a: 1 }>(e: E, key: "a" | "b" | 3): key is keyof E;
export function k2<E extends { a: 1 }>(e: E, key: "a" | "b" | 3) {
  if (isK2(e, key)) { const n: number = key; } else { const m: number = key; }
}
