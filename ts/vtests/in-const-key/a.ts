// in with a constant's name (a string literal type) narrows as the literal does; object members
// get Record<K, unknown>; a unique symbol key reads a symbol index signature
const KEY = 'k';
const S1 = Symbol('s');
export function f(body: object | Date, b2: string | object | undefined, req: object) {
  if (!(KEY in body)) return;
  const e: number = body[KEY];
  if (typeof b2 !== 'object' || b2 === null || !(KEY in b2)) return;
  const e2: number = b2[KEY];
  const r = (req as Record<PropertyKey, unknown>)[S1] === true;
  const r2: number = (req as Record<PropertyKey, unknown>)[S1];
  const r3: number = (req as Record<symbol, string>)[S1];
  return r;
}
