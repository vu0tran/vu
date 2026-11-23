// An array literal whose contextual type is tuple-like (RegExpExecArray has a "0": x ?? [] where x is the context) is a tuple; destructuring a union reads the index's property where a member has one (a too-short tuple adds undefined), else the number index (it adds its elements).
const R0 = /^(\d+)-(.+)$/u;
function f(s: string) {
  const [, a, b] = R0.exec(s) ?? [];
  const t = R0.exec(s) ?? [];
  const [c, d] = s.match(R0) ?? [];
  const u = s.match(R0) ?? [];
  const [e, g] = R0.exec(s) ?? [];
  const z: [number, number, number, number, number, number, number, number] = [a, b, c, d, e, g, t, u];
}
declare const m0: RegExpExecArray | null;
declare const arr: string[] | null;
declare const tup: [number, string] | null;
const t1 = m0 ?? ["a"];
const t2 = arr ?? [];
const t3 = tup ?? [];
const [a1, a2] = arr ?? [];
const [c1, c2] = m0 || ["x", "y"];
const z2: [number, number, number, number, number, number, number] = [t1, t2, t3, a1, a2, c1, c2];
