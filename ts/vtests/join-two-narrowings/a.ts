// Two branches narrowing a reference differently: after the if, the union of the two (it was
// the type from before the if, with the member the else branch threw on).
type Plan =
  | { action: 'a'; p: string | null }
  | { action: 'g'; url: string; p: string }
  | { action: 'u' };
declare function mk(): Plan;
declare function w(): void;
export function f1(): number {
  let plan = mk();
  if (plan.action === 'g') {
    w();
  } else if (plan.action === 'u') {
    throw new Error('x');
  }
  const n: number = plan.p;
  return n;
}
export function f2(x: string | number | boolean): number {
  if (typeof x === 'string') {
    w();
  } else if (typeof x === 'boolean') {
    return 0;
  }
  const n: boolean = x;
  return n ? 1 : 0;
}
export function f3(x: string | number | undefined): number {
  if (typeof x === 'string') {
  } else {
    if (x === undefined) return 0;
  }
  const n: boolean = x;
  return n ? 1 : 0;
}
