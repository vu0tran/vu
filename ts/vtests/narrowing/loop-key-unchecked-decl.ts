declare function deepCopy<T>(s: T): T;
type P = { [k: string]: unknown };
export function f(vals: P | null, names: string[]): P {
  const out: P = {};
  for (const name of names) {
    if (!vals) continue;
    const pv = deepCopy(vals[name]);
    for (const k of Object.keys(pv || {})) {
      out[k] = 1;
    }
  }
  return out;
}
