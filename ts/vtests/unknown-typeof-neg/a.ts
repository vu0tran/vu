export function a(x: unknown): void {
  if (typeof x === 'object') return;
  const t1: number = x;
  if (typeof x === 'undefined') return;
  const t2: number = x;
  if (typeof x === 'string') return;
  const t3: number = x;
}
export function b(x: unknown): void {
  if (typeof x !== 'undefined') { const t4: number = x; } else { const t5: number = x; }
  const t6: number = x;
  if (typeof x === 'object') { const t7: number = x; } else { const t8: number = x; }
  const t9: number = x;
}
export function c(x: unknown): void {
  if (typeof x === 'object' || typeof x === 'undefined') return;
  const u1: number = x;
  if (x == null) return;
  const u2: string = x;
}
export function d(x: unknown): string {
  if (typeof x !== 'object' || x === null) return 'n';
  const u3: number = x;
  return 'y';
