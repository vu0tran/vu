const R = ['a', 'b'] as const;
function en<const U extends string, const T extends Readonly<[U, ...U[]]>>(v: T): T { return v; }
export const e1: readonly ['a', 'b', 'z'] = en([...R, 'u']);
export const e2: readonly ['a', 'b', 'u'] = en([...R, 'u']);
export const t1: [number, string, boolean] = [...[1, 'x'] as [number, string], true];
export const t2: [number, string] = [...[1, 'x'] as [number, string], true];
function mut<const T extends unknown[]>(x: T): T { return x; }
const mv = mut(['p', ['q']]);
export const m2: ['p', readonly ['q']] = mv;
export const m3: ['p', ['q']] = mv;
