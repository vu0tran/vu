type R = { ok: true; result: number } | { ok: false; error: unknown };
function p1(r: R) { return r.ok; }
const p2 = (r: R) => r.ok;
const p3 = (r: R) => r.ok === true;
const p4 = (r: R) => !r.ok;
const p5 = (r: R) => 'result' in r;
const p6 = (r: string | number) => typeof r === 'string';
export const q: 'z' = [p1, p2, p3, p4, p5, p6];
