export function f(p: unknown, q: string) {
  const a = (typeof p === 'string' ? p.trim() : '') || q;
  const b = (p ? '' : null) || q;
  if (p ? 0 : 1) {}
  return [a, b];
}
