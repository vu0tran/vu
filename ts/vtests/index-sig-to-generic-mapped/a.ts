// an object type with index signatures to a generic mapped type { [K in keyof T]: X }: its keys
// are its properties' names alone (keyof S without index signatures), which keyof T doesn't relate
// to, so not related (structuredTypeRelatedTo's generic mapped target)
export {};
function f<T extends object>(o: { [k: string]: any }, p: { [k: string]: any; a: number }, q: { a: number }) {
  const x: { [K in keyof T]: Exclude<T[K], undefined> } = o;
  const y: { [K in keyof T]: T[K] } = p;
  const z: { [K in keyof T]: string } = q;
  const w = o as { [K in keyof T]: Exclude<T[K], undefined> };
}
function g<K extends "a" | "b">(o: { [k: string]: number; a: number; b: number }, r: Record<string, number>) {
  const x: { [P in K]: number } = o;
  const y: { [P in K]: number } = r;
}
function h<T extends object>(obj: T) {
  return Object.fromEntries(Object.entries(obj).filter(([_, value]) => value !== undefined)) as {
    [K in keyof T]: Exclude<T[K], undefined>;
  };
}
