declare const m: Record<string, number | undefined>;
export function f(key: string, keys: string[]) {
  if (m[key] !== undefined) { const q: number = m[key]; }
  for (const k of keys) {
    if (m[k]) { const q2: number = m[k]; }
  }
  let v = 'a';
  if (m[v]) { const q3: number = m[v]; }
  v = 'b';
  const lit = 'x';
  if (m[lit]) { const q4: number = m.x; }
  if (m.y) { const y = 'y' as const; const q5: number = m[y]; }
}
export function g(key: string) {
  key = key + '1';
  if (m[key]) { const q6: number = m[key]; }
}
