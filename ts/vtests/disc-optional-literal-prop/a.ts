interface R { data?: { kind?: 'p'; tag?: string } }
declare const x: R;
export function f() {
  if (x.data?.kind === 'p') {
    return 1;
  }
  const t: number = x.data;
  return 2;
}
interface R2 { data?: { kind: 'p' | 'q'; tag?: string } }
declare const y: R2;
export function g() {
  if (y.data?.kind === 'p') {
    return 1;
  }
  const t: number = y.data;
  return 2;
}
type U = { kind?: 'a'; a: number } | { kind: 'b'; b: string };
declare const u: U;
export function h() {
  if (u.kind === undefined) {
    const t: string = u;
  }
  if (u.kind !== 'a') {
    const w: string = 'a' in u ? u.a : u.b;
  }
}
