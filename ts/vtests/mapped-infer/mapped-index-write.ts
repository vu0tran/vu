export function f<K extends string>(fields: Record<K, number>): Record<K, string> {
  const t = {} as Record<K, string>;
  for (const [field, e] of Object.entries<number>(fields)) {
    t[field as K] = 'x' + e;
  }
  const k = 'a' as K;
  const v: string = t[k];
  const bad: number = t[k];
  return t;
}
