type R = { ok: true; result: number } | { ok: false; error: unknown };
const p3 = (r: R) => r.ok === true;
export const q3: 'z' = p3;
const p5 = (r: R) => 'result' in r;
export const q5: 'z' = p5;
