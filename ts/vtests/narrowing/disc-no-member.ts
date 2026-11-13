type A = { type: 'A'; a: 1 };
type B = { type: 'B'; b: 1 };
export function f(v: A | B, w: A) {
  if (v.type === 'A') {
    if (v.type === 'B') { const z: 'z' = v; }
  }
  if (w.type === 'B') { const z2: 'z' = w; }
}
