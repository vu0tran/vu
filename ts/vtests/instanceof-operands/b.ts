// instanceof: a left side of primitive types only (2358); any on the right narrows nothing
enum E { A, B }
declare const sy: unique symbol;
export function f(e2: string | number, u: unknown, n: never, o: object | string, t: `a${string}`, en: E, s: symbol, v: void, b: boolean, x: string | undefined, a: any) {
  if (e2 instanceof Date) { }
  if (u instanceof Date) { }
  if (o instanceof Date) { }
  if (en instanceof Date) { }
  if (b instanceof Date) { }
  if (x instanceof Date) { }
  if (a instanceof Date) { }
  if (typeof e2 === "string") { if (typeof e2 === "number") { if (e2 instanceof Date) {} } }
  if (1 instanceof Date) {}
}
