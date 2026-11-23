function w3(d: string) {
  if (d) return w3(d);
  return 1;
}
export const z3: string = w3('a');
function w4(d: string) {
  const out = [];
  if (d) out.push(...w4(d));
  out.push(d);
  return out;
}
export const z4: number = w4('a');
function w5(d: string): number {
  return d ? 1 : w5(d);
}
function w6(d: string) {
  const x = w6(d);
  return 1;
}
export const z6: string = w6('a');
function w7(d: string) {
  const out = [];
  if (d) out.push(...w7(d).map((f) => d + f));
  out.push(d);
  return out;
}
export const z7: number = w7('a');
function w8(d: string) {
  const out = [];
  if (d) out.push(w8(d).length);
  out.push(d);
  return out;
}
export const z8: number = w8('a');
