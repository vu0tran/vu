const E = ['a', 'b'];
export const A = [...E, 'x'] as const;
export const z: 'z' = A;
type M = (typeof A)[number];
export const y: 'z' = null as unknown as M;
export const B = [1, ...E, 'x', 2] as const;
export const w: 'z' = B;
export const v: 'z' = B[1];
