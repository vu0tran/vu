// NonNullable<{ [P in K]?: E }[X]>, a generic mapped type indexed by a generic key and made
// non-nullable by ??: the intersection normalized, its T[K] member simplified to E with X for P
// (getNormalizedType, substituteIndexedMappedType), so it relates to E's non-null part
export function g<T extends string>(keys: readonly T[], key: T, d?: Partial<Record<T, string>>) {
  const w1: string = d![key] ?? "";
  const r = d?.[key];
  const w2: string = r ?? "";
  const w3 = keys.map((k) => d?.[k] ?? "-");
  const n: number = w1 + w2;
  return w3;
}
