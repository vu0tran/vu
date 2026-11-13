export function f(xs: number[], ys: string[]) {
  const out = [];
  out.push(...xs);
  out.push(...ys, true);
  const z: 'z' = out;
  return z;
}
