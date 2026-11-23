enum E { A = 'a', B = 'b' }
const m = { [E.A]: 'x', [E.B]: 'y', c: 1 } as const;
export const z1: number = m[E.A];
export const z2: number = m;
