// An object or function source to a generic mapped type { [P in K]: X }: false unless K relates to the source's own keys; with them, its properties there against the template.
declare const fnv: (x: number) => string;
declare const obj: { a: string; b: string };
declare const obj2: { toString(): string };
function f<K extends string, J extends "a" | "b">() {
  const a: Record<K, string> = fnv;
  const b: Record<K, string> = obj;
  const c: Record<J, string> = obj;
  const d: Record<J, number> = obj;
  const g: Record<K, string> | ((x: number) => string) = fnv;
}
