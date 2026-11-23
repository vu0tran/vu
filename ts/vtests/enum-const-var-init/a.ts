export const A = 'aa';
export const B = 'b' + 'c';
const N = 4;
let L = 'x';
const T: string = 'typed';
export enum E {
  X = A,
  Y = B,
  Z = 'z',
}
export enum F {
  P = N,
  Q,
  R = N * 2,
}
const e1: 'aa' = E.X;
const e2: E.Y = E.Y;
const e3: 1 = E.X;
const f1: 5 = F.Q;
const f2: 9 = F.R;
function g(e: E) {
  if (e === E.X) return 1;
  return 2;
}
