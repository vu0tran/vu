declare function p(raw: unknown): unknown;
export function f(x: unknown) {
  const fd = p(x);
  if (fd == null) return null;
  if (typeof fd === 'object' && !Array.isArray(fd)) return 1;
  const q: number = fd;
  return 2;
}
class A { a = 1 }
export function g(y: { b: number } | string) {
  if (typeof y === 'string' || y instanceof A) { const q: number = y; }
}
