// A fresh literal whose regular type is in the other part of a union is removed
// (removeRedundantLiteralTypes): let s = start ?? 'login' is P, not widened to string.
type P = 'login' | 'password';
declare const start: P | undefined;
declare const st2: 'password' | undefined;
let s = start ?? 'login';
let s2 = st2 ?? 'login';
let s4 = Math.random() ? start! : 'login';
const controls: Record<P, string[]> = { login: [], password: [] };
export const f = () => {
  const k: 'x' = s;
  const k2: 'x' = s2;
  const k4: 'x' = s4;
  return [k, k2, k4, controls[s].length];
};
s = 'password';
s2 = 'x';
s4 = 'password';
