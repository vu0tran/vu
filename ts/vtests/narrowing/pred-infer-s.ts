type R = { ok: true; result: number } | { ok: false; error: unknown };
export function f(results: R[]) {
  if (results.every((r) => !r.ok)) { throw results[0].error; }
  const m = results.filter((r) => r.ok).map((r) => r.result);
  const m2 = results.filter((r) => r.ok === true).map((r) => r.result);
  const p = (r: R) => r.ok;
  const q: 'z' = p;
  return [m, m2];
}
