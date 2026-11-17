export {};
type A = { kind: "a"; x: number };
type B = { kind: "b"; y: string };
declare const u: A | B;
if ("start" in u && typeof u.start === "number") {
  const n: string = u.start;
  const k: number = u.kind;
}
if ("start" in u) {
  const s: number = u.start;
  u;
} else {
  const t: A | B = u;
}
function g(v: A | B | null) {
  if (v && "z" in v) { const z: string = v.z; return v.kind; }
  return null;
}
if ("x" in u) { const xx: string = u.x; }
