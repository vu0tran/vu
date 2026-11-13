declare const t: [string | undefined, number | null];
declare const o: { a?: string; 'b-c': number | undefined };
export function f() {
  if (t[0] !== undefined) { const s: string = t[0]; return s; }
  if (t[1]) { const n: number = t[1]; return n; }
  if (o['a']) { const s: string = o.a; return s; }
  if (typeof o['b-c'] === 'number') { const n: number = o['b-c']; return n; }
  if (o.a) { const s: string = o['a']; return s; }
  const s2: string = t[0];
  return s2;
}
let m: { k?: string } = {};
export function g() {
  if (m['k']) { m = {}; const s: string = m['k']; return s; }
  return '';
}
