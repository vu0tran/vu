declare const n: never;
export const c1 = (n || 'a').foo;
export const c2 = (n && 'a').foo;
export const c3 = (n ?? 'a').foo;
declare const nv: never[];
export const c4 = nv.map(({ tok = 'x' }) => tok.foo);
