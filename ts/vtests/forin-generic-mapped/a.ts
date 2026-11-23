export function overrideDeps<T extends Record<string, unknown>>(
  target: T,
  overrides: Partial<T>,
): () => void {
  const originals: Partial<T> = {};
  for (const key in overrides) {
    const k2: number = key;
    originals[key] = target[key];
    (target as Record<string, unknown>)[key] = overrides[key] as unknown;
  }
  return () => {
    for (const key in originals) {
      (target as Record<string, unknown>)[key] = originals[key] as unknown;
    }
  };
}
export function g<T>(x: Readonly<T>, y: { [K in keyof T]?: T[K] }, z: Pick<T, keyof T>, w: Record<keyof T, number>) {
  for (const k in x) { const a: number = k; }
  for (const k in y) { const a: number = k; }
  for (const k in z) { const a: number = k; }
  for (const k in w) { const a: number = k; }
}
