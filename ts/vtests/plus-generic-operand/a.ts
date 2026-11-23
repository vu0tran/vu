type Draft = { a: boolean | null; b: string };
type Field = keyof Draft;
type FR = Record<Field, number>;
export function e<K extends Field>(field: K, fr: FR) {
  const x = fr[field] + 1;
  const q: string = x;
  const o = { ...fr, [field]: fr[field] + 1 };
  const p: string = o;
}
export function g<T extends number, K extends 'a' | 'b'>(t: T, r: { a: 1; b: 2 }[K], s: Record<K, number>[K]) {
  const x = t + 1;
  const q: string = x;
  const y = r + 1;
  const q2: string = y;
  const z = s + 1;
  const q3: string = z;
}
