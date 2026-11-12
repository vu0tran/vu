export function mapRecord<T>(record: Record<string, T>, fn: (value: T) => T): Record<string, T> {
  const next = Object.fromEntries(
    Object.entries(record).map(([key, value]) => {
      const mapped = fn(value);
      return [key, mapped];
    }),
  );
  return next;
}
export function r2(xs: Array<{ score: number }>, f: Record<string, Record<string, number>>) {
  return xs.map(({ score }) => {
    const add = Object.entries(f).reduce((acc, [_, fs]) => acc + (fs["a"] ?? 0), 0);
    return score + add;
  });
}
export function r3(f: Record<string, number>) {
  return Object.entries(f).reduce((acc, [_, n]) => acc + n, 0);
}
export function r4(f: [string, number][]) {
  return f.reduce((acc, [_, n]) => acc + n, 0);
}
export function r5(f: number[]) {
  return f.reduce((acc, n) => acc + n, 0);
}
export function ex(value: string) {
  const regex = /a/g;
  let match;
  while ((match = regex.exec(value)) !== null) { const s: string = match[0]; return s; }
  let m2;
  while ((m2 = regex.exec(value))) { const s: string = m2[0]; return s; }
  return "";
}
declare const u: { length: unknown };
export const z = 1 + u.length;
