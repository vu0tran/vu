enum K { A = 'a', B = 'b' }
const xs = [K.A, K.B];
export const all = [...new Set<K>([...xs])] as const;
const n: number = all;
export const mixed = ['x', ...new Map<string, number>([['a', 1]]), 'y'] as const;
const m: number = mixed;
