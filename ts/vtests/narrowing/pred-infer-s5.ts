type R = { ok: true; result: number } | { ok: false; error: unknown };
function p1(r: R) { return r.ok; }
export const q1: 'z' = p1;
function p0(r: R) { return !r.ok; }
export const q0: 'z' = p0;
