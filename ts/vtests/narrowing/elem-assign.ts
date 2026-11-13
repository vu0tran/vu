declare const t: [string | undefined, number];
declare function u(): string | undefined;
export function f() {
  if (t[0] !== undefined) { t[0] = u(); const s: string = t[0]; return s; }
  if (t[0] !== undefined) { t[0] = 'x'; const s: 'x' = t[0]; return s; }
  if (t[0] !== undefined) { t['0'] = u(); const s: string = t[0]; return s; }
  if (t[0] !== undefined) { (t as any)[0] = u(); const s: string = t[0]; return s; }
  const o = { a: 1 as number | undefined };
  if (o['a'] !== undefined) { o.a = undefined; const n: number = o['a']; return n; }
  if (o.a !== undefined) { delete o['a']; const n: number = o.a; return n; }
  return '';
}
