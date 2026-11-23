// A destructuring parameter's default reads a name before it, and the body reads that name
// first: the pattern is bound for it, and the default reads it with its type (tsc types each
// binding element on its own).
type A = { text: string; variant: 'p' | 'q' };
export const B = ({
  action,
  label = action.text,
  variant = action.variant,
}: { action: A; label?: string; variant?: A['variant'] }) => {
  const t: number = action.text;
  const u: number = label;
  return variant;
};
export function f({ a, b = a.variant }: { a: A; b?: string }) {
  const n: number = a;
  const m: number = b;
}
// (a declaration's pattern, without a type: the default's type is part of b's)
export function g(o: { a: A; b?: number }) {
  const { a, b = a.text } = o;
  const t: number = a.text;
  const u: boolean = b;
}
