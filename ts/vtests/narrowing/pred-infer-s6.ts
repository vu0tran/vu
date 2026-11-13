type R = { ok: true; result: number } | { ok: false; error: unknown };
declare const results: R[];
const isBad = (r: R): r is { ok: false; error: unknown } => !r.ok;
if (results.every(isBad)) { const q: 'z' = results; }
if (results.every((r) => !r.ok)) { const q2: 'z' = results; }
export {};
