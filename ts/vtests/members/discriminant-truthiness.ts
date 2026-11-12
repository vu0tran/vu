type R = { ok: true; value: number } | { ok: false; error: Error };
declare const r: R;
export function f() {
  if (!r.ok) return r.error.message;
  return r.value;
}
export function g(x: { a?: string; k: 1 } | { b: number; k: 2 }) {
  if (x.a) return x.a;
  return 0;
}
type S = { s: "" ; z: 1 } | { s: "x"; y: 2 };
export function h(v: S) { if (v.s) return v.y; return v.z; }
export function i(v: { n: 0; a: 1 } | { n: number; b: 2 }) { if (v.n) return v.b; return 3; }
