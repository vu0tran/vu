// x?.k === "p" with k an optional literal property: k may be undefined, so the false branch
// keeps X (narrowTypeByDiscriminant reads the property's type with undefined in it)
interface X { k?: 'p'; t?: string }
declare const d: X | undefined;
export function g(): number {
  if (d?.k === 'p') return 1;
  const n: number = d?.t;
  return n;
}
export function h(e: X | undefined): number {
  if (e?.k === undefined) {
    const m: number = e;
    return m;
  }
  return 0;
}
type Y = { kind?: 'a'; a: string } | { kind: 'b'; b: number };
export function y(v: Y | undefined): number {
  if (v?.kind !== 'b') {
    const q: number = v;
    return q;
  }
  return v.b;
}
