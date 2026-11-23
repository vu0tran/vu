// an interface's computed key: its expression is checked
export enum T { A = 'a', B = 'b' }
export interface M {
  [T.A]: { x?: number };
  [T.B]: { y: any };
}
export function h(m: M) { const z = m[T.B].y; return z; }
