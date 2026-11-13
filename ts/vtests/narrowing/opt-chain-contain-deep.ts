type P = { k?: string };
export function g(c2: { p: P } | undefined) {
  if (c2?.p.k === 'I') { const z: 'z' = c2; const z2: 'z' = c2.p; }
}
export function h(c2: { p: P } | undefined) {
  if (c2?.p.k !== undefined) { const z: 'z' = c2; }
}
