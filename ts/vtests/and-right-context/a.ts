// the right side of && takes the contextual type (a literal stays a literal there)
interface RD { failedBeforeStart?: true; kind?: 'a' | 'b'; n: number }
export function f(failed: boolean, k: string) {
  const r: RD = { n: 1, ...(failed && { failedBeforeStart: true }) };
  const r2: RD = { n: 1, ...(k && { kind: 'a' }) };
  const r3: RD = { n: 1, ...(failed && { kind: 'c' }) };
  const t: 'x' | false = failed && 'x';
  const u: 'x' | false = failed && 'y';
  const fn: ((s: string) => number) | false = failed && ((s) => s.length);
  return [r, r2, r3, t, u, fn];
}
