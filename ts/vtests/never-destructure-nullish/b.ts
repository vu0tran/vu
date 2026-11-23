export const b2 = ({ reqs = [] }) => reqs.map(({ tok }) => tok.foo);
export const b3 = ({ reqs = [] }) => reqs.map(({ tok }) => (tok ?? '').foo);
declare const nv: never[];
export const b4 = nv.map(({ tok }) => (tok ?? '').foo);
export const b5 = nv.map((r) => r.foo);
export const b6 = nv.map(({ tok = 'x' }) => tok.length);
