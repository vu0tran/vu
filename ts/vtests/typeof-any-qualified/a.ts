// typeof x.a.b where x is any (an unresolved import's type): any
import { X } from 'nope-mod';
export function f(c: X) {
  const v = 1 as unknown as typeof c.oauth.token;
  const w: typeof c.a = 3;
  const n: number = v;
  return [v, w];
}
