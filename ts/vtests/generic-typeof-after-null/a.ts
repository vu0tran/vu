// T narrowed by !== null, then typeof: T & undefined's typeof is "undefined"
declare function fail(m: string): never;
export const p1 = <T>(s: string): T => {
  let parsed: T;
  try {
    parsed = JSON.parse(s);
  } catch {
    throw fail('x');
  }
  if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw fail('y');
  }
  const n: number = parsed;
  return parsed;
};
export const p2 = <T>(v: T): T => {
  if (v === null || typeof v !== 'object') throw fail('y');
  const n: number = v;
  return v;
};
export const p3 = (s: string): number => {
  let parsed: string | number;
  try { parsed = JSON.parse(s); } catch { throw fail('x'); }
  const n: boolean = parsed;
  return 1;
};
