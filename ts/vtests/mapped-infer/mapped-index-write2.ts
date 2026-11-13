export function f<K extends string, T>(k: K, p: Partial<Record<K, string>>, r: Record<K, T>, v: T, u: T | undefined) {
  p[k] = 'x';
  p[k] = undefined;
  p[k] = 1;
  r[k] = v;
  r[k] = u;
  const q: { [P in K]: P } = {} as any;
  q[k] = k;
  q[k] = 'a';
}
