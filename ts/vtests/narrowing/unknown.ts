export function f1(v: unknown) {
  if (v === null || typeof v === "string") return 0;
  if (typeof v === "object") { const o: object = v; return o; }
  return 1;
}
export function f2(v: unknown) {
  if (v !== null && v !== undefined) { const o: {} = v; return o; }
  return 1;
}
export function f3(v: unknown) {
  if (v == null) return 0;
  const o: {} = v;
  return o;
}
export function f4(v: unknown) {
  switch (typeof v) {
    case "string": { const s: string = v; return s; }
    case "number": return v + 1;
    case "boolean": return v ? 1 : 0;
  }
  return 2;
}
export function f5(v: unknown) {
  if (v === undefined) return 0;
  const x: number = v;
  return x;
}
